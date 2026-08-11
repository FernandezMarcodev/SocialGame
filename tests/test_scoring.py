"""Tests del modulo de puntuacion (RF-PUN-001 a 004)."""

import pytest

from app.api.errors import ApiError
from app.domain.entities import PlayerRef, Room, Turn, Vote
from app.services.match_service import MatchService
from app.services.scoring_service import ScoringService
from app.stores.memory import MemoryMatchStore, MemoryRoomStore
from tests.test_auth import auth_headers
from tests.test_turns import match_and_turn


class TestScoringHttp:
    def test_scoreboard_empty_at_start(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        resp = client.get(
            f"/api/v1/matches/{match_id}/scoreboard", headers=auth_headers(author_tok)
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["round"] == 0
        ids = [
            client.get("/api/v1/users/me", headers=auth_headers(t)).json()["id"]
            for t in [author_tok, voters[0]]
        ]
        assert data["scores"] == {ids[0]: 0, ids[1]: 0}

    def test_scoreboard_updates_after_turn(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 3)
        me = client.get("/api/v1/users/me", headers=auth_headers(author_tok)).json()
        author_id = me["id"]
        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero corro despacio", "secret_score": 7},
            headers=auth_headers(author_tok),
        )
        assert resp.status_code == 200, resp.text
        for i, score in enumerate([7, 7, 3][: len(voters)]):
            resp = client.post(
                f"/api/v1/matches/{match_id}/votes",
                json={"score": score},
                headers=auth_headers(voters[i]),
            )
            assert resp.status_code == 200, resp.text
        resp = client.get(
            f"/api/v1/matches/{match_id}/scoreboard", headers=auth_headers(author_tok)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["scores"][author_id] == 2

    def test_result_requires_finished(self, client, outbox):
        _, match_id, author_tok, _ = match_and_turn(client, outbox, 2)
        resp = client.get(
            f"/api/v1/matches/{match_id}/result", headers=auth_headers(author_tok)
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "MATCH_NOT_FINISHED"

    def test_result_winner_after_round(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        voter_tok = voters[0]
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero como lento", "secret_score": 6},
            headers=auth_headers(author_tok),
        )
        client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 6}, headers=auth_headers(voter_tok)
        )
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero sueno", "secret_score": 4},
            headers=auth_headers(voter_tok),
        )
        client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 2}, headers=auth_headers(author_tok)
        )
        resp = client.get(
            f"/api/v1/matches/{match_id}/result", headers=auth_headers(author_tok)
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        author1 = client.get("/api/v1/users/me", headers=auth_headers(author_tok)).json()["id"]
        assert data["winner_id"] == author1
        assert data["tied"] is False
        assert data["scores"][author1] == 1

    def test_result_tie(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        voter_tok = voters[0]
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "a frase uno", "secret_score": 5},
            headers=auth_headers(author_tok),
        )
        client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 5}, headers=auth_headers(voter_tok)
        )
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "a frase dos", "secret_score": 5},
            headers=auth_headers(voter_tok),
        )
        client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 5}, headers=auth_headers(author_tok)
        )
        resp = client.get(
            f"/api/v1/matches/{match_id}/result", headers=auth_headers(author_tok)
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["winner_id"] is None
        assert data["tied"] is True

    def test_scoring_endpoints_require_auth(self, client):
        resp = client.get("/api/v1/matches/m-111/scoreboard")
        assert resp.status_code == 401


class TestScoringService:
    def test_turn_points_exact_matches(self):
        scoring, match, turn = _scoring_setup(["u1", "u2", "u3"])
        _finish_turn(turn, secret=6, values=[6, 2])
        scoring.apply_turn(turn, match)
        assert scoring.turn_points(turn) == 1
        assert turn.points == 1
        assert match.scores["u1"] == 1

    def test_turn_points_no_matches(self):
        scoring, match, turn = _scoring_setup(["u1", "u2", "u3"])
        _finish_turn(turn, secret=6, values=[1, 2])
        scoring.apply_turn(turn, match)
        assert scoring.turn_points(turn) == 0
        assert match.scores["u1"] == 0

    def test_turn_points_requires_finished_voting(self):
        scoring, match, turn = _scoring_setup(["u1", "u2"])
        with pytest.raises(ApiError) as exc:
            scoring.turn_points(turn)
        assert exc.value.code == "TURN_NOT_FINISHED"

    def test_scoreboard_shape(self):
        scoring, match, turn = _scoring_setup(["u1", "u2", "u3"])
        _finish_turn(turn, secret=6, values=[6, 2])
        scoring.apply_turn(turn, match)
        scoring._matches.advance_round(match.match_id)
        data = scoring.scoreboard(match.match_id)
        assert data["round"] == 1
        assert data["scores"] == {"u1": 1, "u2": 0, "u3": 0}

    def test_result_delegates_to_match(self):
        scoring, match, turn = _scoring_setup(["u1", "u2"])
        _finish_turn(turn, secret=6, values=[6])
        scoring.apply_turn(turn, match)
        scoring._matches.advance_round(match.match_id)
        scoring._matches.finish_round(match.match_id)
        result = scoring.result(match.match_id)
        assert result["winner_id"] == "u1"


def _scoring_setup(players):
    mstore, rstore = MemoryMatchStore(), MemoryRoomStore()
    matches = MatchService(matches=mstore, rooms=rstore)
    scoring = ScoringService(matches=matches)
    room = Room(
        code="AB12CD",
        creator_id="u1",
        modality_id=1,
        state="available",
        players=[PlayerRef(id=p, username=p, joined_at=1) for p in players],
        min_players=2,
        max_players=6,
        created_at=1,
    )
    rstore.add(room)
    match = matches.create_match(room, "u1")
    matches.initialize_match(match.match_id)
    match.turn_order = list(players)
    matches.start_first_turn(match.match_id)
    turn = Turn(
        turn_id="t-1",
        match_id=match.match_id,
        author_id="u1",
        state="active",
        phrase=None,
        secret_score=None,
        created_at=1,
        expires_at=2,
        voting_ends_at=None,
        votes=[],
    )
    return scoring, match, turn


def _finish_turn(turn, *, secret, values):
    turn.state = "voting"
    turn.phrase = "Es un 10 pero algo"
    turn.secret_score = secret
    for i, value in enumerate(values):
        turn.votes.append(Vote(voter_id=f"u{i + 2}", value=value))
    turn.state = "finished"
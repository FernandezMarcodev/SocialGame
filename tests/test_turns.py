"""Tests del módulo de turnos (RF-TUR-001 a 011)."""

import pytest

from app.api.errors import ApiError
from app.core.config import Settings
from app.domain.entities import PlayerRef, Room
from app.services.match_service import MatchService
from app.services.scoring_service import ScoringService
from app.services.turn_service import TurnService
from app.stores.memory import MemoryMatchStore, MemoryRoomStore, MemoryTurnStore
from tests.test_auth import auth_headers
from tests.test_matches import start_match_http


def match_and_turn(client, outbox, amount=2):
    tokens, room_code, match_id = start_match_http(client, outbox, amount)
    data = client.get(f"/api/v1/matches/{match_id}", headers=auth_headers(tokens[0])).json()
    author_id = data["turn_order"][0]
    ids = [
        client.get("/api/v1/users/me", headers=auth_headers(t)).json()["id"]
        for t in tokens
    ]
    author_tok = tokens[ids.index(author_id)]
    voters = [t for t in tokens if t != author_tok]
    return tokens, match_id, author_tok, voters


def get_match(client, token, match_id):
    resp = client.get(f"/api/v1/matches/{match_id}", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


def get_turn(client, token, match_id, turn_id):
    resp = client.get(f"/api/v1/matches/{match_id}/turns/{turn_id}", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    return resp.json()


class TestTurnHttp:
    def test_full_round_two_players(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        voter_tok = voters[0]

        turn1_id = get_match(client, author_tok, match_id)["current_turn"]
        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero todavía programo en Java", "secret_score": 5},
            headers=auth_headers(author_tok),
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["turn_id"] == turn1_id

        voting = get_turn(client, voter_tok, match_id, turn1_id)
        assert voting["state"] == "voting"
        assert voting["phrase"] == "Es un 10 pero todavía programo en Java"
        assert voting["secret_score"] is None
        assert voting["votes"] == []

        resp = client.post(
            f"/api/v1/matches/{match_id}/votes",
            json={"score": 5},
            headers=auth_headers(voter_tok),
        )
        assert resp.status_code == 200, resp.text

        after = get_match(client, voter_tok, match_id)
        assert after["current_turn"] != turn1_id
        turn2_id = after["current_turn"]

        result1 = get_turn(client, author_tok, match_id, turn1_id)
        assert result1["state"] == "finished"
        assert result1["secret_score"] == 5
        assert result1["votes"] == [{"voter_id": result1["votes"][0]["voter_id"], "value": 5}]
        assert result1["points"] == 1

        author2 = client.get("/api/v1/users/me", headers=auth_headers(voter_tok)).json()["id"]
        turn2 = get_turn(client, author_tok, match_id, turn2_id)
        assert turn2["author_id"] == author2
        assert turn2["state"] == "active"

        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero duermo con el celu", "secret_score": 7},
            headers=auth_headers(voter_tok),
        )
        assert resp.status_code == 200, resp.text
        resp = client.post(
            f"/api/v1/matches/{match_id}/votes",
            json={"score": 3},
            headers=auth_headers(author_tok),
        )
        assert resp.status_code == 200, resp.text

        final = get_match(client, author_tok, match_id)
        assert final["state"] == "finished"
        author1 = client.get("/api/v1/users/me", headers=auth_headers(author_tok)).json()["id"]
        assert final["scores"] == {author1: 1, author2: 0}

        resp = client.get(f"/api/v1/rooms/{final['room_code']}", headers=auth_headers(author_tok))
        assert resp.status_code == 404

    def test_phrase_wrong_author(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero golpeo la mesa", "secret_score": 4},
            headers=auth_headers(voters[0]),
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_AUTHOR"

    def test_duplicate_phrase(self, client, outbox):
        _, match_id, author_tok, _ = match_and_turn(client, outbox, 2)
        payload = {"phrase": "Es un 10 pero me baño los domingos", "secret_score": 6}
        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase", json=payload, headers=auth_headers(author_tok)
        )
        assert resp.status_code == 200
        resp = client.post(
            f"/api/v1/matches/{match_id}/phrase", json=payload, headers=auth_headers(author_tok)
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_SUBMITTED"

    def test_author_cannot_vote(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero como fideos", "secret_score": 3},
            headers=auth_headers(author_tok),
        )
        resp = client.post(
            f"/api/v1/matches/{match_id}/votes",
            json={"score": 3},
            headers=auth_headers(author_tok),
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "NOT_VOTING"

    def test_vote_before_phrase(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 2)
        resp = client.post(
            f"/api/v1/matches/{match_id}/votes",
            json={"score": 3},
            headers=auth_headers(voters[0]),
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "NOT_VOTING"

    def test_duplicate_vote(self, client, outbox):
        _, match_id, author_tok, voters = match_and_turn(client, outbox, 3)
        client.post(
            f"/api/v1/matches/{match_id}/phrase",
            json={"phrase": "Es un 10 pero ronco fuerte", "secret_score": 8},
            headers=auth_headers(author_tok),
        )
        resp = client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 5}, headers=auth_headers(voters[0])
        )
        assert resp.status_code == 200, resp.text
        resp = client.post(
            f"/api/v1/matches/{match_id}/votes", json={"score": 5}, headers=auth_headers(voters[0])
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "ALREADY_VOTED"

    def test_outside_user_cannot_see_turn(self, client, outbox):
        tokens, match_id, author_tok, _ = match_and_turn(client, outbox, 2)
        outsider = _register_outsider(client, outbox)
        turn_id = get_match(client, author_tok, match_id)["current_turn"]
        resp = client.get(
            f"/api/v1/matches/{match_id}/turns/{turn_id}", headers=auth_headers(outsider)
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "NOT_IN_MATCH"

    def test_turn_endpoints_require_auth(self, client):
        resp = client.post("/api/v1/matches/m-111/votes", json={"score": 1})
        assert resp.status_code == 401
        resp = client.get("/api/v1/matches/m-111/turns/t-222")
        assert resp.status_code == 401


class TestTurnServiceUnit:
    def _clock(self, ms=1_700_000_000_000):
        class Clock:
            def __init__(self, t):
                self._t = t

            def __call__(self):
                return self._t

            def advance(self, step_ms):
                self._t += step_ms

        return Clock(ms)

    def _setup(self, players=("u1", "u2"), order=None):
        clock = self._clock()
        settings = Settings(_env_file=None)
        mstore, rstore = MemoryMatchStore(), MemoryRoomStore()
        matches = MatchService(matches=mstore, rooms=rstore, now=clock)
        scoring = ScoringService(matches=matches)
        turns = TurnService(
            settings=settings,
            matches=matches,
            turns=MemoryTurnStore(),
            scoring=scoring,
            now=clock,
        )
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
        match.turn_order = list(order if order is not None else players)
        turn = turns.start_match(match.match_id)
        return clock, matches, turns, match, turn

    def test_author_timeout_discards_and_advances(self):
        clock, matches, turns, match, turn = self._setup(["u1", "u2"])
        assert turn.author_id == "u1"
        assert turn.state == "active"
        clock.advance(2 * 60_000)
        with pytest.raises(ApiError) as exc:
            turns.submit_phrase("u1", match.match_id, "Es un 10 pero tardo", 5)
        assert exc.value.code == "TURN_EXPIRED"
        assert turn.state == "discarded"
        nxt = turns.get_turn(match.current_turn)
        assert nxt.author_id == "u2"

    def test_voting_timeout_finalizes_and_advances(self):
        clock, matches, turns, match, turn = self._setup(["u1", "u2"])
        turns.submit_phrase("u1", match.match_id, "Es un 10 pero llego tarde", 5)
        clock.advance(2 * 30_000)
        with pytest.raises(ApiError) as exc:
            turns.submit_vote("u2", match.match_id, 5)
        assert exc.value.code == "TURN_FINISHED"
        assert turn.state == "finished"
        assert matches.get_match(match.match_id).current_turn != turn.turn_id

    def test_settle_expired_advances(self):
        clock, matches, turns, match, turn = self._setup(["u1", "u2"])
        clock.advance(2 * 60_000)
        turns.settle_expired(match.match_id)
        assert turn.state == "discarded"
        assert matches.get_match(match.match_id).current_turn != turn.turn_id

    def test_points_only_exact_matches(self):
        clock, matches, turns, match, turn = self._setup(["u1", "u2", "u3"])
        turns.submit_phrase("u1", match.match_id, "Es un 10 pero grito", 5)
        turns.submit_vote("u2", match.match_id, 5)
        turns.submit_vote("u3", match.match_id, 3)
        assert turn.state == "finished"
        assert turn.points == 1
        assert matches.get_match(match.match_id).scores["u1"] == 1

    def test_full_round_finishes_with_winner(self):
        clock, matches, turns, match, turn = self._setup(["u1", "u2"], order=["u1", "u2"])
        turns.submit_phrase("u1", match.match_id, "Es un 10 pero como", 5)
        turns.submit_vote("u2", match.match_id, 5)
        turn2 = turns.get_turn(match.current_turn)
        assert turn2.author_id == "u2"
        turns.submit_phrase("u2", match.match_id, "Es un 10 pero duermo", 7)
        turns.submit_vote("u1", match.match_id, 3)
        after = matches.get_match(match.match_id)
        assert after.state == "finished"
        assert after.scores == {"u1": 1, "u2": 0}
        result = matches.result(match.match_id)
        assert result["winner_id"] == "u1"
        assert result["tied"] is False


def _register_outsider(client, outbox):
    from tests.test_auth import verified_login

    return verified_login(client, outbox, "outsider", "outsider@example.com")
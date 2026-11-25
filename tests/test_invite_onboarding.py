import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from invite_onboarding import InviteGate, SellerSignup


class RecordingClient:
    def __init__(self):
        self.requests = []

    def create_user(self, request):
        self.requests.append(request)
        return {"id": "seller-123"}


def signup(code):
    return SellerSignup("seller@example.com", "secret", "Mina", code, ["handmade mugs"], "signup-123")


def test_unknown_invite_is_rejected_before_account_creation():
    client = RecordingClient()
    result = InviteGate(client, {"BUILD-2026"}).onboard(signup("NOPE-0000"))

    assert result == {"status": "rejected", "reason": "invite_code_required"}
    assert client.requests == []


def test_invited_seller_is_created_with_assets_attached_to_result():
    client = RecordingClient()
    result = InviteGate(client, {"BUILD-2026"}).onboard(signup("BUILD-2026"))

    assert result["status"] == "accepted"
    assert result["user"]["id"] == "seller-123"
    assert result["assets"] == ["handmade mugs"]

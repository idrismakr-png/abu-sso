
from collections import defaultdict

from authlib.oauth2.rfc6749 import OAuth2Payload, OAuth2Request
from starlette.requests import Request


class StarletteOAuth2Payload(OAuth2Payload):
    """Adapt Starlette query/form data to Authlib's OAuth2 payload interface."""

    def __init__(self, multidict):
        self._data = dict(multidict)
        self._datalist = defaultdict(list)

        for key, value in multidict.multi_items():
            self._datalist[key].append(value)

    @property
    def data(self):
        return self._data

    @property
    def datalist(self):
        return self._datalist


class ABUOAuth2Request(OAuth2Request):
    """OAuth2 request compatible with FastAPI and Starlette."""

    def __init__(self, request, payload, form_data=None, db=None):
        super().__init__(
            method=request.method,
            uri=str(request.url),
            headers=dict(request.headers),
        )

        self.payload = StarletteOAuth2Payload(payload)
        self._args = request.query_params
        self._form_data = form_data or {}
        self.database_session = db

    @property
    def args(self):
        return self._args

    @property
    def form(self):
        return self._form_data


async def create_oauth2_request(
    request: Request,
    db=None,
) -> ABUOAuth2Request:
    """Convert a FastAPI request and attach its database session."""

    form_data = {}

    if request.method.upper() == "POST":
        form_data = await request.form()
        payload = form_data
    else:
        payload = request.query_params

    return ABUOAuth2Request(
        request=request,
        payload=payload,
        form_data=form_data,
        db=db,
    )

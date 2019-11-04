# -*- coding: utf-8 -*-
import re
import urllib
import urllib.parse
from unittest import mock

import pytest  # type: ignore

from coupons import webtopay


def test_build_request_no_projectid() -> None:
    # Exception should be thrown if project id is not given

    data = {
        "orderid": "123",
        "accepturl": "http://local.test/accept",
        "cancelurl": "http://local.test/cancel",
        "callbackurl": "http://local.test/callback",
        "sign_password": "asdfghjkl",
    }
    with pytest.raises(webtopay.WebToPayException) as excinfo:
        webtopay.build_request(data)
    assert "sign_password or projectid is not provided" in str(excinfo.value)


def test_build_request() -> None:
    rq = webtopay.build_request(
        {
            "orderid": 123,
            "amount": 100,
            "some-other-parameter": "abc",
            "cancelurl": "http://local.test/",
            "accepturl": "http://local.test/",
            "callbackurl": "http://local.test/",
            "projectid": "123",
            "sign_password": "secret",
        }
    )
    assert rq["sign"] == b"2aad3564f048109bd0878b2a12653ed1"
    assert rq["data"].startswith(b"YWNjZXB0dXJsPWh0d")
    assert rq["data"].endswith(b"JnZlcnNpb249MS42")


def test_prepare_query_string() -> None:
    data = {
        "orderid": 123,
        "amount": 100,
        "some-other-parameter": "abc",
        "cancelurl": "http://local.test/",
        "accepturl": "http://local.test/",
        "callbackurl": "http://local.test/",
        "paytext": "U\u017esakymas",
    }
    qs = webtopay._prepare_query_string(data, "123")

    expected = (
        "orderid=123&accepturl=http%3A%2F%2Flocal.test%2F&"
        "cancelurl=http%3A%2F%2Flocal.test%2F&"
        "callbackurl=http%3A%2F%2Flocal.test%2F&"
        "paytext=U%C5%BEsakymas&amount=100&"
        "some-other-parameter=abc&version=1.6&projectid=123"
    )

    # Expected and produced query strings should be the same
    assert urllib.parse.parse_qs(expected) == urllib.parse.parse_qs(qs)


def test_response() -> None:
    qs = (
        "data=b3JkZXJpZD0xJmxhbmc9bGl0JnByb2plY3RpZD0zMDQzMiZjdXJyZ"
        "W5jeT1MVEwmYW1vdW50PTMwMDAwJnZlcnNpb249MS42JmNvdW50cnk9TFQ"
        "mdGVzdD0xJnR5cGU9RU1BJnBheW1lbnQ9aGFuemEmcGF5dGV4dD1VJUM1J"
        "UJFc2FreW1hcytuciUzQSsxK2h0dHAlM0ElMkYlMkZ3d3cuc2tsYW5keW1"
        "hcy5sdCtwcm9qZWt0ZS4rJTI4UGFyZGF2JUM0JTk3amFzJTNBK0RhbGlhK"
        "1ZhaW5pZW4lQzQlOTclMjkmcF9lbWFpbD1hbmRyZXkubGViZWRldiU0MGd"
        "tYWlsLmNvbSZwX2NvdW50cnluYW1lPSZzdGF0dXM9MSZyZXF1ZXN0aWQ9M"
        "zQ0NjM5ODQmbmFtZT1VQUImc3VyZW5hbWU9TW9rJUM0JTk3amltYWkubHQ"
        "mcGF5YW1vdW50PTMwMDAwJnBheWN1cnJlbmN5PUxUTA%3D%3D&ss1=e450"
        "da330163deb38ec21ecc601c7125&ss2=B1AqKhD0nycSYhKvc60cYQvhs"
        "-HPUt4r4kP7KrKOe77TVtg6G7GvRMhZ5fXruMPlDkg_ia2EqhGYzYGLQrj"
        "EL2H2Db5_UiKKQSSqwrjE_Kka1h-mYVl6_ulM43uz87MQeYwh3DMRhoHx3"
        "uih6Q3QqvqXypLY1tXZN2sDHFJIFGQ%3D"
    )

    qsplain = urllib.parse.unquote(qs)
    data = dict(urllib.parse.parse_qsl(qsplain))

    with pytest.raises(webtopay.WebToPayException) as excinfo:
        webtopay.validate_and_parse_data(data, "badproject", "badsig")
    assert "Signature ss1 is not valid" in str(excinfo.value)

    # Mock signature checker to test parsing
    with mock.patch("coupons.webtopay._is_valid_ss1") as m:
        m.return_value = True
        with pytest.raises(webtopay.WebToPayException) as excinfo:
            webtopay.validate_and_parse_data(data, "21", "")

        assert "Bad project id: 30432, should be: 21" in str(excinfo.value)

    with mock.patch("coupons.webtopay._is_valid_ss1") as m:
        m.return_value = True
        request = webtopay.validate_and_parse_data(data, "30432", "")

        # Check some of the attributes with personal data separately
        assert re.match(r"andrey.*@gmail.com", request["p_email"])
        del request["p_email"]
        assert re.match(
            r"Užsakymas nr: 1 http://www.sklandymas.lt projekte. \(Pardavėjas: .*\)",
            request["paytext"],
        )
        del request["paytext"]

        # Check the rest of the attributes
        expected = {
            "amount": "30000",
            "country": "LT",
            "currency": "LTL",
            "lang": "lit",
            "name": "UAB",
            "orderid": "1",
            "payamount": "30000",
            "paycurrency": "LTL",
            "payment": "hanza",
            "projectid": "30432",
            "requestid": "34463984",
            "status": "1",
            "surename": "Mokėjimai.lt",
            "test": "1",
            "type": "macro",
            "version": "1.6",
        }
        assert expected == request

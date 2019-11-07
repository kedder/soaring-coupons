# Soaring Coupons

[![Build Status](https://travis-ci.org/kedder/soaring-coupons.png?branch=master)](https://travis-ci.org/kedder/soaring-coupons)
[![Coverage Status](https://coveralls.io/repos/kedder/soaring-coupons/badge.png)](https://coveralls.io/r/kedder/soaring-coupons)

Soaring Coupons is a basic application that is capable of organizing sales of
pre-defined items through mokejimai.lt payment provider.

## Running

Simplest way to run the app is to use [docker](https://www.docker.com/) and
[docker-compose](https://docs.docker.com/compose/). In order to start the app,
copy `env.sample` file into `env` and edit it to provide necessary
configuration. Then do:

```sh
docker-compose up
```

The app should be available on http://localhost:8080. Django admin is available
under `/dbadmin` url.

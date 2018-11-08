# Changelog

## 0.6.10 release (2018-11-08)

* Depends on pyramid_apispec==0.3.0

## 0.6.9 release (2018-11-02)

0.6 BRANCH IS THE LAST RELEASE THAT SUPPORTS
PYTHON OLDER THAN 3.6

* Demos are now standalone applications
* Added request validation with Marshmallow schemas
* Added API Explorer under /api-explorer
* Added edit and delete message API's
* Uses itsdangerous 1.1.0 for signing, to support 0.24 version additional
  config option `validate_requests` to allow disabling timestamp checks
*
* Bugfixes

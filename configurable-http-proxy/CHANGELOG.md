# Changes in configurable-http-proxy

For detailed changes from the prior release, click on the version number, and
its link will bring up a GitHub listing of changes. Use `git log` on the
command line for details.

## [Unreleased]

## [4.2.1] - 2020-03-11

#### Summary

This is a security release, fixing node package dependencies to
configurable-http-proxy, which itself was left untouched.

#### Merged PRs

- Security Fixes [#226](https://github.com/jupyterhub/configurable-http-proxy/pull/226) ([@rafael-ladislau](https://github.com/rafael-ladislau))
- Update dependency commander to ~4.1.0 [#225](https://github.com/jupyterhub/configurable-http-proxy/pull/225) ([@renovate](https://github.com/renovate))

## [4.2.0] - 2019-11-14

#### Summary

- Now terminates on `SIGTERM` as can be caused by `docker stop` or `kubectl delete`
- Add `--timeout` option to configure when to drop a request
- Add `--custom-header` option that enables proxied requests to get additional headers attached
- Support setting of the environment variable `CONFIGPROXY_AUTH_TOKEN` using a mounted file on the Docker image's container
- Node version bumped from 10 to 12.13.0 in the Docker image
- Various dependencies updated, including addressing security advisories from `npm audit` which do not affect CHP security itself.

#### Merged PRs

- RELEASE.md documentation and small fixes [#220](https://github.com/jupyterhub/configurable-http-proxy/pull/220) ([@consideRatio](https://github.com/consideRatio))
- Terminate on SIGTERM [#217](https://github.com/jupyterhub/configurable-http-proxy/pull/217) ([@consideRatio](https://github.com/consideRatio))
- Fix Vulnerabilities [#216](https://github.com/jupyterhub/configurable-http-proxy/pull/216) ([@rafael-ladislau](https://github.com/rafael-ladislau))
- Update dependency commander to v4 [#214](https://github.com/jupyterhub/configurable-http-proxy/pull/214) ([@renovate](https://github.com/renovate))
- chore: Udpate node, replace add with copy [#213](https://github.com/jupyterhub/configurable-http-proxy/pull/213) ([@jgwerner](https://github.com/jgwerner))
- Update dependency http-proxy to ~1.18.0 [#212](https://github.com/jupyterhub/configurable-http-proxy/pull/212) ([@renovate](https://github.com/renovate))
- Change user to numeric value for k8s compatibility [#211](https://github.com/jupyterhub/configurable-http-proxy/pull/211) ([@m2hofi94](https://github.com/m2hofi94))
- Add file_env function to set the token env var [#209](https://github.com/jupyterhub/configurable-http-proxy/pull/209) ([@rcthomas](https://github.com/rcthomas))
- Allow setting request timeout [#208](https://github.com/jupyterhub/configurable-http-proxy/pull/208) ([@archite](https://github.com/archite))
- Command line option for custom headers [#206](https://github.com/jupyterhub/configurable-http-proxy/pull/206) ([@ivan-gomes](https://github.com/ivan-gomes))
- chore(deps): update dependency nyc to v14 [#202](https://github.com/jupyterhub/configurable-http-proxy/pull/202) ([@renovate](https://github.com/renovate))
- Update dependency commander to ~2.20.0 [#201](https://github.com/jupyterhub/configurable-http-proxy/pull/201) ([@renovate](https://github.com/renovate))

## [4.1.0] - 2019-04-01

- Add `--redirect-to` option to specify destination port when redirecting
  http to https with `--redirect-from`.
- Add health check endpoint at `/_chp_healthz`.
- Docker base image is updated to `node/10-alpine` from `node/6-alpine`
- Dependencies are updated via Renovate

## [4.0.0] - 2018-10-12

- Add support for client SSL certificates for encrypting proxied requests.
- Update all nodejs dependencies. Most significant is updating winston (logging) from 2 to 3. There is no longer a global logger,
  instead use `this.log`.
- Drop support for node 4. Minimum node version is 6.
- Support CONFIGPROXY_SSL_KEY_PASSPHRASE env for setting the passphrase of ssl keys (API_SSL for api ssl key).

## [3.1.1] - 2018-01-15

- Fix a bug when using the new custom storage backend support
  where the body of requests could be lost.

## [3.1.0] - 2017-11-03

3.1 adds two new features:

- Add `--change-origin` passthrough for node-http-proxy's changeOrigin option.
- Add support via `--storage-backend <storage-class>` for custom storage classes.
  See [configurable-http-proxy-redis-backend](https://github.com/globocom/configurable-http-proxy-redis-backend)
  for an example using redis.

## [3.0.0] - 2017-09-19

3.0 is a major release because much of the code has been reorganized
to adopt some javascript standards:

- Use ES6 and Promises instead of ES5 and callbacks,
  which we can do without a compiler because CHP 2.0 required nodejs < 4.
- auto-format code with prettify (run `npm run fmt` to auto-format your code after making changes).

There shouldn't be any major changes in 3.0, but marking it as a major upgrade because
there could be regressions introduced by the restructuring.

Fixes:

- Fix routing of `/prefix?query` where a query parameter was passed
  exactly on the routing prefix with no trailing slash.

Improvements:

- Quieter messages for ECONNREFUSED and ECONNRESET,
  which are generally not indicative of problems,
  but rather common events of peers disconnecting during a request.
- The docker image for `jupyterhub/configurable-http-proxy`
  is now based on `node:6-alpine`.

## [2.0] - 2017-04-05

### 2.0.4 - 2017-06-21

- Add logging of all API requests

### 2.0.3 - 2017-06-12

- Fix docker image entrypoint, broken in 2.0.2

### 2.0.2 - 2017-06-07

- Fix error raised trying to `setHeader` on an undefined response (e.g. when encountering socket-level error)

### 2.0.1

**Important** CHP 2.0.0 drops support for node.js ≤ 4.0.

**Added:**

- Add configuration option for proxy timeout `--proxy-timeout <n>, Timeout
  (in millis) when proxy receives no response from target.`
  [\#86](https://github.com/jupyterhub/configurable-http-proxy/pull/86)
- Add configuration options for auto rewrite and protocol rewrite
  [\#73](https://github.com/jupyterhub/configurable-http-proxy/pull/73):
    - `--auto-rewrite, Rewrite the Location header host/port in redirect responses`
    - `--protocol-rewrite <proto>', Rewrite the Location header protocol in redirect responses to the specified protocol`
- Add low-level code for separate stores of routes to enable future support of other data stores such as Redis [\#81](https://github.com/jupyterhub/configurable-http-proxy/pull/81)

**Changed:**

- Support only LTS releases and above for NodeJS [\#82](https://github.com/jupyterhub/configurable-http-proxy/pull/82).
  This means only ≥ 4.0 are supported.

**Fixed:**

- Fix behavior to correctly handle children when a parent node is deleted [\#93](https://github.com/jupyterhub/configurable-http-proxy/pull/93)
- Fix closure reference when serving custom error pages [\#91](https://github.com/jupyterhub/configurable-http-proxy/pull/91)
- Improved all-interfaces warning message when `ip='*'`  [\#94](https://github.com/jupyterhub/configurable-http-proxy/pull/94)

## [1.3] - 2016-08-01

### 1.3.1

- small fixes for node 6 support
- fix `--no-x-forward` again (for real, this time)

### 1.3.0

- add `--ssl-protocol`, so that one can restrict to TLS, e.g. `--ssl-protocol=TLSv1`
- fix handling of ``--no-x-forward`

## [1.2] - 2016-04-19

- add statsd support

## [1.1] - 2016-01-04

- add `--ssl-request-cert` args for certificate-based client authentication
- fix some SSL parameters that were ignored for API requests

## [1.0] - 2016-01-04

- add `ConfigProxy.proxy_request` event, for customizing requests as the pass through the proxy.
- add more ssl-related options for specifying options on the CLI.
- fix regression in 0.5 where deleting a top-level route would also delete the default route.

## [0.5] - 2015-10-05

- add `--error-target` for letting another http server render error pages.
  Server must handle `/404` and `/503` URLs.
- add `--error-path` for custom static HTML error pages.
  `[CODE].html` will be used if it exists, otherwise `error.html`.
- fix bug preventing root route from being deleted

## [0.4] - 2015-10-02

- add `--redirect-port` for automatically redirecting a common port to the correct one (e.g. redirecting http to https)

## [0.3] - 2015-04-29

- fixes for URL escaping
- add host-based routing

## [0.2.1] - 2014-11-21

## [0.2.0] - 2014-11-14

## 0.1.1 - 2014-10-01

[Unreleased]: https://github.com/jupyterhub/configurable-http-proxy/compare/4.1.0...HEAD
[4.1]: https://github.com/jupyterhub/configurable-http-proxy/compare/4.0.1...4.1.0
[4.0]: https://github.com/jupyterhub/configurable-http-proxy/compare/3.1.1...4.0.1
[3.1.1]: https://github.com/jupyterhub/configurable-http-proxy/compare/3.1.0...3.1.1
[3.1]: https://github.com/jupyterhub/configurable-http-proxy/compare/3.0.0...3.1.0
[3.0]: https://github.com/jupyterhub/configurable-http-proxy/compare/2.0.4...3.0.0
[2.0]: https://github.com/jupyterhub/configurable-http-proxy/compare/1.3.1...2.0.4
[1.3]: https://github.com/jupyterhub/configurable-http-proxy/compare/1.2.0...1.3.0
[1.2]: https://github.com/jupyterhub/configurable-http-proxy/compare/1.1.0...1.2.0
[1.1]: https://github.com/jupyterhub/configurable-http-proxy/compare/1.0.0...1.1.0
[1.0]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.5.0...1.0.0
[0.5]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.4.0...0.5.0
[0.4]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.3.0...0.4.0
[0.3]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.2.1...0.3.0
[0.2.1]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.2.0...0.2.1
[0.2.0]: https://github.com/jupyterhub/configurable-http-proxy/compare/0.1.1...0.2.0

# forge-useragent

Forked version of [fake-useragent](https://github.com/fake-useragent/fake-useragent).

- Supports Python 3.10 or higher

## Introduction

### Installation

```sh
# pypi name change to `forge-useragent`
pip install forge-useragent

# check version
pip list | grep -i forge-useragent
python -c "import fake_useragent; print(fake_useragent.__version__)"
```

### Usage

package name is same `fake_useragent`:

```py
from fake_useragent import UserAgent
ua = UserAgent()

# Get a random browser user-agent string
print(ua.random)

# Or get user-agent string from a specific browser
print(ua.chrome)
print(ua.firefox)
print(ua.safari)
print(ua.opera)
print(ua.edge)

print(ua['Chrome'])
```

### More

```py
# names are case-sensitive!
from fake_useragent import UserAgent

# browsers
ua = UserAgent(browsers=['Edge', 'Chrome'])
ua.random

# os
ua = UserAgent(os='Linux')
ua.random

# platforms: desktop / mobile / tablet
ua = UserAgent(platforms='mobile')
ua.random

from fake_useragent import UserAgent
ua = UserAgent(platforms='desktop')
ua.random

# get only user agents that have a minimum version of 120.0:
from fake_useragent import UserAgent
ua = UserAgent(min_version=120.0)
ua.random
```

### User-agent Python Dictionary

> **Warning**
> Raw JSON objects (in a Python dictionaries) are returned "as is".
> Meaning, this data structure could change in the future!
>
> Be aware that these "get" properties below might not return the same key/value pairs in the future.
> Use `ua.random` or alike as mentioned above, if you want to use a stable interface.
>
> **INCOMPATIBLE** PROPERTY NAME CHANGED!

```py

from fake_useragent import UserAgent
ua = UserAgent()

# Random user-agent dictionary (object)
ua.get_random # old version: ua.getRandom

# More get properties:
ua.get_f_irefox # ua.getFirefox
ua.get_chrome   # ua.getChrome
ua.get_safari   # ua.getSafari
ua.get_edge     # ua.getEdge

# And a method with an argument.
ua.get_browser('firefox') # ua.getBrowser('firefox')
```

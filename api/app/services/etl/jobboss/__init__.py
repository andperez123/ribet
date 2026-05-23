"""JobBOSS-specific parsers — same as generic with stricter column maps for v1."""

from app.services.etl.generic.parser import PARSERS

# JobBOSS exports use standard column names; reuse generic with alias maps
JOBBOSS_PARSERS = PARSERS

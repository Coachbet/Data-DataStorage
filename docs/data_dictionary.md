# Data dictionary and operational definitions

This file is intentionally started before data collection. Update it whenever a
variable is added or redefined.

| Concept | Operational definition | Raw fields required | Limitation |
|---|---|---|---|
| Department vote share | Candidate votes divided by valid votes in a department and round | candidate votes, valid votes, department, round, year | Aggregate measure; not an individual probability |
| Abstention rate | Registered voters who did not vote divided by registered voters | registered voters, voters, department, round, year | Registration and turnout changes may affect comparisons |
| Candidate transfer | Estimated share of an eliminated candidate's first-round support allocated to each finalist or abstention | harmonised round results and explicit estimation assumptions | Ecological estimate; individual choices are unobserved |
| Political bloc | Documented mapping from candidate to a fixed analytical category | candidate identifier, year, mapping version | Classification is subjective and can change over time |

## Required identifiers

- election year;
- round;
- candidate identifier and display name;
- commune and department codes using the applicable INSEE geography;
- registered voters, voters, blank ballots, null ballots, valid votes and candidate votes.

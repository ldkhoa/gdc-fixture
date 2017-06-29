This is a clone of GoodSales template 2 which is going to be deprecated. It's worth to mention that the fixture has no business objects (e.g.: dashboards, reports, metrics, and so on). We experienced many times that our needs were changed rapidly. For that reason, any change on fixture to fulfill our needs requires a lot of testing effort.

To solve our problem, the fixture is aiming to automation tests only (mainly used in Graphene tests). In details, providing fixture utility methods to create common business objects is the way to use this one.

The following is some additional value it brings into:

1. avoid duplicated code for creating same object in test classes and maintain easily when changes are required
2. improve significantly script readability because required data/object is mentioned in tests.
3. make test author pay attention to identify/create common object for further use

Note: reference ticket: https://jira.intgdc.com/browse/QA-6438

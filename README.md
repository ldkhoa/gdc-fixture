# Common fixtures for GoodData tests
New approach to fixtures - instead of using deprecated project template
functionality, projects will be created via public API, using model
defined as MAQL DDL and data defined as a set of CVS files and upload manifest.

Fixtures are language-agnostic, it is up to fixture consumers to implement in their favorite programming language a trivial steps needed to use the fixture ([see below](#how-to-use-the-fixture)).

## Project fixtures
See [fixtures/README.md] for details.

* `fixtures/` - contains all fixtures
  * `FixtureName/` - contains all versions of given fixtures
    * `version/` - contains files for specific version of fixtures
      * `model.maql` - logical data model definition in [MAQL DDL](https://developer.gooddata.com/article/maql-ddl)
      * `metadata.json` - definition of MD objects (see [fixture documentation]
      (fixtures/README.md)).
      * `dataset.csv` - one or many CSV files, containing data for datasets defined via MAQL DDL
      * `upload_info.json` - upload manifest, containing [dataSetSLIManifestList](https://developer.gooddata.com/article/multiload-of-csv-data), describes how CSV files and columns in them match dataset and their attributes.
* `tools` - automation and testing tools
  * `zip-upload.sh` - creates `upload.zip` file containing CVS files and `upload_info.json` for given fixture.
  * `validate_json` - validates given JSON file against the JSON schema (draft-03)



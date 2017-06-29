# Fixture structure and how to apply
## 1. Fixture structure
* `fixtures/` - contains all fixtures
  * `FixtureName/` - contains all versions of given fixtures
    * `version/` - contains files for specific version of fixtures
      * `model.maql` - logical data model definition in [MAQL DDL](https://developer.gooddata.com/article/maql-ddl)
      * `metadata.json` - definition of MD objects (see below).
      * `dataset.csv` - one or many CSV files, containing data for datasets defined via MAQL DDL
      * `upload_info.json` - upload manifest, containing [dataSetSLIManifestList](https://developer.gooddata.com/article/multiload-of-csv-data), describes how CSV files and columns in them match dataset and their attributes.


### 1.1. model.maql
Defines logical data model (datasets, fact, attributes and their display 
forms).
Each LDM object in MAQL DDL is referred with the identifier, like:
```model.maql
CREATE DATASET {dataset.issue_reason} VISUAL(TITLE "Hotfix reasons N:M");
```
`{dataset.issue_reason}` is such identifier.

Fixture consumer could collect all the identifiers with the following 
regular expression: `{([\w\.]*)}`

To get the URIs of LDM objects, you should POST to  
`/gdc/md/<project>/identifiers` resource (see below).

### 1.2. metadata.json
Defines the MD objects to be created and date dimensions for which we should
 to get identifiers of the attributes and display forms.
```metadata.json
{
  "import_identifiers": [
    "created_on.act81lMifn6q"
  ],
  "objects": [
    {
      "name": "metric_count_hotfix_reason_id",
      "content": {
        "metric": {
          "meta": {
            "title": "# of Hotfix reason ID",
            "summary": "",
            "tags": "",
            "deprecated": 0,
            "unlisted": 1
          },
          "content": {
            "expression": "SELECT COUNT([{{attr_issue_reason_reason_issue}}])",
            "format": "#,##0.00",
            "folders": []
          }
        }
      }
    }
  ]
}
```
#### 1.2.1. metadata.json/import_identifiers
List of identifiers for objects from included dimensions 
(typically date dimensions).
Example:
* In ```model.maql```, you may define multiple date dimensions based on 
standard GoodData date dimension template. Each line like below creates a 
copy of dataset in your project:
```
INCLUDE TEMPLATE "URN:GOODDATA:DATE" MODIFY (IDENTIFIER "created_on", TITLE "Created On");
```
* Some of your MD objects may refer some display form of attribute from
`created_on` standard date dimension, like `act81lMifn6q`. Add this 
identifier to `import_identifiers`:
```metadata.json
"import_identifiers": [
    "created_on.act81lMifn6q"
  ],
```

You should use `/gdc/md/<project>/identifiers` to retrieve object URIs in 
the same way was for LDM objects (see below).

#### 1.2.2. metadata.json/objects
An array of MD object definitions, each item should contain:
* `name`: the name of the object, which could be used to refer object in 
other objects
* `content`: object definition, the payload to be POSTed to 
`/gdc/md/<project>/obj` resource.

Object definitions are [mustache](https://mustache.github.io/) templates, with 
placeholders for referred object URIs, like:
```metadata.json
  {
      "name": "report_hotfix_reasons_per_release",
      "content": {
        "report": {
          "content": {
            "domains": [
            ],
            "definitions": [
              "{{hotfix_reasons_per_release_report_definition}}"
            ]
          },
          "meta": {
            "title": "Hotfix reasons per release",
            "summary": "",
            "tags": "",
            "deprecated": 0,
            "unlisted": 1,
            "locked": 0
          }
        }
      }
    }
```
`hotfix_reasons_per_release_report_definition` refers to previously defined 
report definition.
Important note: replace all periods (".") in referred identifiers with
underscores ("_").

### 1.3. upload_info.json
Upload manifest, containing [dataSetSLIManifestList](https://developer.gooddata.com/article/multiload-of-csv-data)
Describes how CSV files and columns in them match dataset and their attributes.

### 1.4. \<dataset\>.csv
CSV file(s) containing data for each dataset. 

## 2. How to use the fixture
Using public API and your favourite programming language, you can create a 
testing project with the steps described below. Sample python implementation
 [is provided](../tools/deploy_fixture).

### 2.1. Create an empty project
POST at `/gdc/project`:
```javascript
{
  "project": {
      "content": {
          "guidedNavigation": "1",
          "driver": "Pg",
          "authorizationToken": "<project_group>",
          "environment": "TESTING"
      },
      "meta": {
          "title": "<your project title>",
          "summary": "<your project summary>"
      }
  }
}
```
Poll resulting `/gdc/project/<project_id>` until field `project.content.state`
has value `ENABLED`

### 2.2. Create logical data model
Get the content of `model.maql` file from the fixture you need (`/fixtures/FixtureName/version/`)
POST at `/gdc/md/<project_id>/ldm/manage2`:
```javascript
{"manage":
  { "maql": "<content of model.maql>" }
}
```
Poll the URI returned as `entries.[0].link` in response, until field
`wTaskStatus.status` has value `OK`.

### 2.3. Upload the data
* Create `upload.zip` file with all CVS files and `upload_info.json` in your fixture.
You can use provided `tools/zip-upload.sh` for that, but you don't have to.
* Create a directory at WebDAV:
`MKCOL /uploads/<unique_name_of_the_upload>/`
* Upload `upload.zip`: `PUT /uploads/<unique_name_of_the_upload>/upload.zip`

### 2.4. Call ETL pull task
To get data into the project, you should POST at `/gdc/md/<project_id>/etl/pull2`:
```javascript
{"pullIntegration": "<unique_name_of_the_upload>"}
```
Poll the URI returned as `pull2Task.links.poll` until field
`wTaskStatus.status` has value `OK`.

### 2.5. Apply metadata fixture
#### 2.5.1. Acquire URIs for each LDM object
* Parse out each identifier from MAQL using regexp `{([\w\.]*)}`
* Prepare the payload for `/gdc/md/<project>/identifiers` resource:
```POST
{
    "identifierToUri": [
        "identifier.number1",
        ...
        "identifier.numberN",
    ]
}
```
* Parse the response into dictionary, replacing `.` with `_` in identifiers 
(to be used by `mustache` templates):
```response
{
    "identifiers": [
        {
            "identifier": "identifier.number1",
            "uri": "/gdc/md/<project>/obj/<numeric_id_1>"
        },
        ...
        {
            "identifier": "identifierN",
            "uri": "/gdc/md/<project>/obj/<numeric_id_N>"
        }

    ]
}
```
Refer to documentation of [`mustache`](https://mustache.github.io/)
implementation for your language about the data structure.
For python it is a `dict`: 
```dict
{'identifier1': '/gdc/md/<project>/obj/<numeric_id_1>',
'identifier2': '/gdc/md/<project>/obj/<numeric_id_2>'}
```
#### 2.5.2. Acquire URIs for included dimension objects
If you include dimensions from templates (typically date dimensions),
pass the list of `import_identifiers` to POST on `/gdc/md/<project>/identifiers` 
For example:
```POST
{
    "identifierToUri": [
        "created_on.aag81lMifn6q",
        ...
        "created_od.year",
        "closed_on.aag81lMifn6q",
        ...
        "closed_on.year",
    ]
}
```
Parse the response, add the result to the dictionary from the previous step 
(you can join them to POST only once).

#### 2.5.3. Create MD objects
For each item in `metadata.json/objects` do:
* render `content` template via `mustache` using identifier to uri translation
 dictionary you prepared in the steps above. All placeholders should be 
 replaced by the real object URIs
* POST the prepared payload to `/gdc/md/<project>/obj?createAndGet=true`
* From the response, fetch URI from `<root object>/meta/uri` field
* Add pair `name:uri` to your translation dictionary
 
 
 Now you have your project ready.
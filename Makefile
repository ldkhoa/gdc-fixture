FIXTURES := $(filter %/, $(wildcard fixtures/*/*/))

default: .test/bin/jsonschema

.test/bin/activate:
	@virtualenv .test

.PHONY: venv
venv: .test/bin/activate

.test/bin/cram: .test/bin/activate
	@. .test/bin/activate && \
	pip install cram
	
.test/bin/jsonschema: .test/bin/activate
	@. .test/bin/activate && \
	pip install jsonschema==2.5.1

.test/bin/pystache: .test/bin/activate
	@. .test/bin/activate && \
	pip install pystache

.PHONY: test-cram
test-cram: .test/bin/cram
	mkdir -p out
	source .test/bin/activate && \
	cram --xunit-file=out/cram.xml ./fixtures/SingleInvoice/

.PHONY: test
test-json: .test/bin/jsonschema
	@mkdir -p out	
	@. .test/bin/activate && \
	for fixture in $(FIXTURES); do \
		tools/validate_json fixtures/upload_info_schema.json \
		$$fixture/upload_info.json ; \
	done \
	&& deactivate

test-json-ci: .test/bin/jsonschema
	@mkdir -p out	
	@. .test/bin/activate && \
	for fixture in $(FIXTURES); do \
		tools/validate_json fixtures/upload_info_schema.json \
		$$fixture/upload_info.json  \
		  $$(echo $$fixture | sed 's:/:.:g;s,^,out/,;s,$$,xml,') ; \
	done \
	&& deactivate

.PHONY: test test-ci
test: test-json test-cram
test-ci: test-json-ci test-cram

.PHONY: zip
zip:
	@for fixture in $(FIXTURES); do \
		echo "zipping $$fixture:" ; \
		tools/zip-upload.sh $$fixture; \
	done

.PHONY: clean
clean:
	@rm -f fixtures/*/*/upload.zip
	@rm -rf out
	@rm -rf .test

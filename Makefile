help:
	@echo	"MAKE TARGETS"
	@echo	"clean        -- remove generated files"
	@echo	"ext          -- build C extensions"
	@echo 	"docs         -- build Sphinx docs"
	@echo 	"help         -- this text"
	@echo   "pot          -- update pot"

genned_files=\
	'*.egg-info' \
	'*.gcda' \
	'*.gcno' \
	'*.gcov' \
	'*.o' \
	'*.orig' \
	'*.py[cdo]' \
	'*.so' \
	'*.tmp' \
	'*~' \
	'.eggs' \
	'.tox' \
	'__pycache__' \
	'_build' \
	'apsw' \
	'build' \
	'dist' \
	'duplicity*.rst' \
	'megatestresults' \
	'testdb*' \
	'testextension.sqlext' \
	'testing*.rst' \
	'work'

clean:
	for i in ${genned_files}; do \
		find . -name "$$i" | xargs -t -r rm -rf ; \
	done
	find . -name 'S.*' -type s -delete

docs:
	sphinx-apidoc -o docs/ --separate --private . \
		apsw duplicity/backends/pyrax_identity/* setup.* testing/overrides testing/manual
	$(MAKE) -C docs html

ext:
	./setup.py build_ext

pot:
	po/update-pot

.PHONY: clean docs ext help pot

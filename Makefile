help:
	@echo	"MAKE TARGETS"
	@echo	"clean        -- remove generated files"
	@echo	"ext          -- build C extensions"
	@echo 	"docs         -- build Sphinx docs"
	@echo 	"help         -- this text"
	@echo   "pot          -- update duplicity.pot"
	@echo   "sdist        -- make versioned source"

genned_files=\
	'*.egg-info' \
	'*.gcda' \
	'*.gcno' \
	'*.gcov' \
	'*.o' \
	'*.orig' \
	'*.py[cdo]' \
	'*.tmp' \
	'*~' \
	'.eggs' \
	'.pytest_cache' \
	'.tox' \
	'__pycache__' \
	'_build' \
	'apsw' \
	'build' \
	'dist' \
	'duplicity*.rst' \
	'librsync*.so' \
	'megatestresults' \
	'report.xml' \
	'testdb*' \
	'testextension.sqlext' \
	'testing*.rst' \
	'wheelhouse' \
	'work'

clean:
	for i in ${genned_files}; do \
		find . -name "$$i" | xargs -t -r rm -rf ; \
	done
	find . -name 'S.*' -type s -delete

docs:
	sphinx-apidoc -o docs/ --separate --private . \
		apsw duplicity/backends/pyrax_identity/* setup.* testing/overrides testing/manual
ifndef READTHEDOCS
	$(MAKE) -C docs html
endif

ext:
	python3 ./setup.py build_ext

pot:
	po/update-pot

sdist:
	python3 ./setup.py -q sdist

.PHONY: clean docs ext help pot sdist

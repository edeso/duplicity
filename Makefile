help:
	@echo	"MAKE TARGETS"
	@echo 	"help         -- this text"
	@echo	"clean        -- remove generated files"
	@echo 	"docs         -- build Sphinx docs"
	@echo	"ext          -- build C extensions"
	@echo   "xlate-export -- update pot and make tar to export to LP translators"
	@echo   "xlate-import -- process LP tranlator's export file into duplicity"

clean:
	for i in '.tox' '_build' 'build' 'dist' 'apsw' 'work' 'megatestresults' '.eggs' '*.egg-info' \
		'__pycache__' '*.pyc' '*.pyo' '*~' '*.o' '*.so' '*.pyd' '*.gcov' '*.gcda' \
		'*.gcno' '*.orig' '*.tmp' 'testdb*' 'testextension.sqlext' \
		'duplicity*.rst' 'testing*.rst'; do \
		find . -name "$$i" | xargs -t -r rm -rf ; \
	done
	find . -name 'S.*' -type s -delete

docs:
	sphinx-apidoc -o docs/ --separate --private . \
		apsw duplicity/backends/pyrax_identity/* setup.* testing/overrides testing/manual
	$(MAKE) -C docs html

ext:
	./setup.py build_ext

.PHONY: clean docs ext help

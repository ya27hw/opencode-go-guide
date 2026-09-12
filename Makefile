BASE ?= https://ya27hw.github.io/opencode-go-guide

.PHONY: verify verify-local verify-wait serve

verify: ## verify the deployed site (canonical check after any change)
	python3 tools/check_live_site.py --base $(BASE)

verify-wait: ## same, but poll for the first GitHub Pages build
	python3 tools/check_live_site.py --base $(BASE) --wait 300

verify-local: ## offline sanity check on the source files
	python3 tools/check_local.py

serve: ## local preview at http://localhost:8080
	python3 -m http.server 8080

BASE ?= https://ya27hw.github.io/opencode-go-guide

.PHONY: verify verify-wait verify-local assets og serve

verify: ## verify the deployed site (canonical check after any change)
	python3 tools/check_live_site.py --base $(BASE)

verify-wait: ## same, but poll until every deployed path has propagated
	python3 tools/check_live_site.py --base $(BASE) --wait 300

verify-local: ## offline source checks for both pages
	python3 tools/check_local.py

assets: ## rebuild hero images (WebP + fallback) and the social card
	python3 tools/optimize_images.py
	python3 tools/make_og_image.py

serve: ## local preview at http://localhost:8080
	python3 -m http.server 8080

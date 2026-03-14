.PHONY: dev dev-down dev-logs prod-up prod-down

dev:
	docker compose --profile dev up app-dev frontend-dev

dev-down:
	docker compose --profile dev down

dev-logs:
	docker compose --profile dev logs -f app-dev frontend-dev

prod-up:
	docker compose up app

prod-down:
	docker compose down

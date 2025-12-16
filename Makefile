.PHONY: build up down logs help

help:
	@echo "Available commands:"
	@echo "  make build    - Build Docker images"
	@echo "  make up       - Start services in background"
	@echo "  make down     - Stop services"
	@echo "  make logs     - View logs"
	@echo "  make clean    - Stop and remove volumes"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v

#!/bin/bash

echo "🚀 Setting up SkillMap Nepal..."

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual credentials"
fi

# Build Docker containers
echo "🐳 Building Docker containers..."
docker-compose build

# Start services
echo "🔧 Starting services..."
docker-compose up -d db redis

# Wait for database
echo "⏳ Waiting for database..."
sleep 5

# Run migrations
echo "📊 Running migrations..."
docker-compose run --rm web python manage.py makemigrations
docker-compose run --rm web python manage.py migrate

# Create superuser (optional)
echo "👤 Create superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    docker-compose run --rm web python manage.py createsuperuser
fi

# Collect static files
echo "📦 Collecting static files..."
docker-compose run --rm web python manage.py collectstatic --noinput

# Start all services
echo "🎉 Starting all services..."
docker-compose up -d

echo "✅ Setup complete!"
echo ""
echo "🌐 Access the application:"
echo "   - Web: http://localhost"
echo "   - Admin: http://localhost/admin"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: docker-compose logs -f"
echo "   - Stop services: docker-compose down"
echo "   - Restart: docker-compose restart"
echo "   - Scrape jobs: docker-compose exec web python manage.py scrape_jobs"
echo ""

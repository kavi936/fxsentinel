#!/usr/bin/env python3
"""
Simple SQLite Web Viewer for Economic Calendar Database
Opens a web interface to browse your economic calendar data
"""

import sqlite3
import json
from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Economic Calendar Database Viewer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 24px; font-weight: bold; color: #1976d2; }
        .stat-label { color: #666; margin-top: 5px; }
        .search-box { margin: 20px 0; }
        .search-box input { width: 300px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
        .search-box button { padding: 10px 20px; background: #1976d2; color: white; border: none; border-radius: 4px; cursor: pointer; margin-left: 10px; }
        .events-table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        .events-table th, .events-table td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        .events-table th { background: #f5f5f5; font-weight: bold; }
        .events-table tr:nth-child(even) { background: #f9f9f9; }
        .impact-high { background: #ffebee !important; }
        .impact-medium { background: #fff3e0 !important; }
        .impact-low { background: #e8f5e8 !important; }
        .pagination { margin: 20px 0; text-align: center; }
        .pagination button { margin: 0 5px; padding: 8px 12px; border: 1px solid #ddd; background: white; cursor: pointer; }
        .pagination button.active { background: #1976d2; color: white; }
        .loading { text-align: center; padding: 20px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Economic Calendar Database Viewer</h1>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number" id="total-events">-</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="high-impact">-</div>
                <div class="stat-label">High Impact</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="currencies">-</div>
                <div class="stat-label">Currencies</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="date-range">-</div>
                <div class="stat-label">Date Range</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="search-input" placeholder="Search events (e.g., CPI, GDP, Employment)" />
            <button onclick="searchEvents()">Search</button>
            <button onclick="loadEvents()">Show All</button>
        </div>

        <div id="loading" class="loading" style="display: none;">Loading events...</div>
        
        <table class="events-table" id="events-table" style="display: none;">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Time</th>
                    <th>Event</th>
                    <th>Currency</th>
                    <th>Impact</th>
                    <th>Previous</th>
                    <th>Expected</th>
                    <th>Actual</th>
                </tr>
            </thead>
            <tbody id="events-tbody">
            </tbody>
        </table>

        <div class="pagination" id="pagination" style="display: none;">
            <button onclick="previousPage()">Previous</button>
            <span id="page-info">Page 1 of 1</span>
            <button onclick="nextPage()">Next</button>
        </div>
    </div>

    <script>
        let currentPage = 1;
        const pageSize = 50;
        let totalPages = 1;

        // Load statistics on page load
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                document.getElementById('total-events').textContent = data.total_events.toLocaleString();
                document.getElementById('high-impact').textContent = data.high_impact_events.toLocaleString();
                document.getElementById('currencies').textContent = data.currencies_count;
                document.getElementById('date-range').textContent = data.date_range;
            });

        // Load events
        function loadEvents(page = 1, search = '') {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('events-table').style.display = 'none';
            
            fetch(`/api/events?page=${page}&limit=${pageSize}&search=${encodeURIComponent(search)}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('events-table').style.display = 'table';
                    
                    const tbody = document.getElementById('events-tbody');
                    tbody.innerHTML = '';
                    
                    data.events.forEach(event => {
                        const row = document.createElement('tr');
                        row.className = `impact-${event.impact}`;
                        row.innerHTML = `
                            <td>${event.date || '-'}</td>
                            <td>${event.time || '-'}</td>
                            <td>${event.title}</td>
                            <td>${event.currency || '-'}</td>
                            <td>${event.impact}</td>
                            <td>${event.previous_value || '-'}</td>
                            <td>${event.expected_value || '-'}</td>
                            <td>${event.actual_value || '-'}</td>
                        `;
                        tbody.appendChild(row);
                    });
                    
                    currentPage = data.page;
                    totalPages = data.total_pages;
                    updatePagination();
                });
        }

        function searchEvents() {
            const search = document.getElementById('search-input').value;
            currentPage = 1;
            loadEvents(1, search);
        }

        function nextPage() {
            if (currentPage < totalPages) {
                loadEvents(currentPage + 1, document.getElementById('search-input').value);
            }
        }

        function previousPage() {
            if (currentPage > 1) {
                loadEvents(currentPage - 1, document.getElementById('search-input').value);
            }
        }

        function updatePagination() {
            const pageInfo = document.getElementById('page-info');
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
            
            const prevBtn = document.querySelector('.pagination button:first-child');
            const nextBtn = document.querySelector('.pagination button:last-child');
            
            prevBtn.disabled = currentPage === 1;
            nextBtn.disabled = currentPage === totalPages;
            
            document.getElementById('pagination').style.display = totalPages > 1 ? 'block' : 'none';
        }

        // Load initial events
        loadEvents();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/stats')
def get_stats():
    try:
        conn = sqlite3.connect('economic_calendar.db')
        cursor = conn.cursor()
        
        # Total events
        cursor.execute('SELECT COUNT(*) FROM economic_events')
        total_events = cursor.fetchone()[0]
        
        # High impact events
        cursor.execute('SELECT COUNT(*) FROM economic_events WHERE impact = "high"')
        high_impact_events = cursor.fetchone()[0]
        
        # Currencies count
        cursor.execute('SELECT COUNT(DISTINCT currency) FROM economic_events WHERE currency IS NOT NULL AND currency != ""')
        currencies_count = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(date), MAX(date) FROM economic_events WHERE date IS NOT NULL AND date != ""')
        date_range = cursor.fetchone()
        date_range_str = f"{date_range[0]} to {date_range[1]}" if date_range[0] else "No dates"
        
        conn.close()
        
        return jsonify({
            'total_events': total_events,
            'high_impact_events': high_impact_events,
            'currencies_count': currencies_count,
            'date_range': date_range_str
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/events')
def get_events():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        search = request.args.get('search', '')
        
        offset = (page - 1) * limit
        
        conn = sqlite3.connect('economic_calendar.db')
        cursor = conn.cursor()
        
        # Build query
        where_clause = ""
        params = []
        
        if search:
            where_clause = "WHERE title LIKE ?"
            params.append(f'%{search}%')
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM economic_events {where_clause}"
        cursor.execute(count_query, params)
        total_events = cursor.fetchone()[0]
        total_pages = (total_events + limit - 1) // limit
        
        # Get events
        query = f"""
            SELECT date, time, title, currency, impact, previous_value, expected_value, actual_value
            FROM economic_events 
            {where_clause}
            ORDER BY date DESC, time DESC
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(query, params)
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'date': row[0],
                'time': row[1],
                'title': row[2],
                'currency': row[3],
                'impact': row[4],
                'previous_value': row[5],
                'expected_value': row[6],
                'actual_value': row[7]
            })
        
        conn.close()
        
        return jsonify({
            'events': events,
            'page': page,
            'total_pages': total_pages,
            'total_events': total_events
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🌐 Starting Economic Calendar Database Viewer...")
    print("📊 Open your browser and go to: http://localhost:5002")
    print("🛑 Press Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=5002, debug=True)

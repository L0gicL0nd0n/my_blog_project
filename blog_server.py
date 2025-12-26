# blog_server.py - Pure Python web server, NO Flask needed!
import http.server
import socketserver
import sqlite3
from datetime import datetime
import html

PORT = 8000

# Initialize database
conn = sqlite3.connect('blog.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS articles
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              content TEXT NOT NULL,
              created_at TIMESTAMP)''')
conn.commit()

# Add sample data if empty
c.execute("SELECT COUNT(*) FROM articles")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO articles (title, content, created_at) VALUES (?, ?, ?)",
              ("Welcome to My Blog", "This is your first article. Edit it or create new ones!", 
               datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()

conn.close()

class BlogHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/articles' or self.path == '/':
            self.show_articles()
        elif self.path == '/articles/create':
            self.show_create_form()
        elif self.path.startswith('/articles/') and self.path.endswith('/edit'):
            article_id = self.path.split('/')[2]
            self.show_edit_form(article_id)
        else:
            self.send_error(404, "Page not found")
    
    def do_POST(self):
        if self.path == '/articles/create':
            self.create_article()
        elif self.path.startswith('/articles/') and '/edit' in self.path:
            article_id = self.path.split('/')[2]
            self.update_article(article_id)
    
    def show_articles(self):
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("SELECT * FROM articles ORDER BY created_at DESC")
        articles = c.fetchall()
        conn.close()
        
        articles_html = ""
        for article in articles:
            articles_html += f'''
            <div style="border:1px solid #ddd; padding:15px; margin:10px 0;">
                <h3>{html.escape(article[1])}</h3>
                <p>{html.escape(article[2][:100])}...</p>
                <small>Created: {article[3]}</small><br>
                <a href="/articles/{article[0]}/edit">Edit</a>
            </div>
            '''
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>My Blog</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                nav {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
            </style>
        </head>
        <body>
            <h1>My Blog</h1>
            <nav>
                <a href="/articles">All Articles</a> | 
                <a href="/articles/create">Create Article</a>
            </nav>
            
            <h2>All Articles</h2>
            {articles_html if articles else "<p>No articles yet. <a href='/articles/create'>Create first article!</a></p>"}
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def show_create_form(self):
        html_content = '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Create Article</title>
            <style>
                body { font-family: Arial; margin: 40px; }
                input, textarea { width: 100%; padding: 10px; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h1>Create New Article</h1>
            <nav>
                <a href="/articles">← Back to Articles</a>
            </nav>
            
            <form method="POST" action="/articles/create">
                <input type="text" name="title" placeholder="Title" required><br>
                <textarea name="content" rows="10" placeholder="Content" required></textarea><br>
                <button type="submit">Save Article</button>
                <a href="/articles">Cancel</a>
            </form>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def show_edit_form(self, article_id):
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("SELECT * FROM articles WHERE id=?", (article_id,))
        article = c.fetchone()
        conn.close()
        
        if not article:
            self.send_error(404, "Article not found")
            return
        
        html_content = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Edit Article</title>
            <style>
                body {{ font-family: Arial; margin: 40px; }}
                input, textarea {{ width: 100%; padding: 10px; margin: 5px 0; }}
            </style>
        </head>
        <body>
            <h1>Edit Article</h1>
            <nav>
                <a href="/articles">← Back to Articles</a>
            </nav>
            
            <form method="POST" action="/articles/{article_id}/edit">
                <input type="text" name="title" value="{html.escape(article[1])}" required><br>
                <textarea name="content" rows="10" required>{html.escape(article[2])}</textarea><br>
                <button type="submit">Update Article</button>
                <a href="/articles">Cancel</a>
            </form>
        </body>
        </html>
        '''
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
    
    def create_article(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        params = {}
        for pair in post_data.split('&'):
            key, value = pair.split('=')
            params[key] = html.escape(value.replace('+', ' '))
        
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO articles (title, content, created_at) VALUES (?, ?, ?)",
                  (params['title'], params['content'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        self.send_response(302)  # Redirect
        self.send_header('Location', '/articles')
        self.end_headers()
    
    def update_article(self, article_id):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Parse form data
        params = {}
        for pair in post_data.split('&'):
            key, value = pair.split('=')
            params[key] = html.escape(value.replace('+', ' '))
        
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("UPDATE articles SET title=?, content=? WHERE id=?", 
                  (params['title'], params['content'], article_id))
        conn.commit()
        conn.close()
        
        self.send_response(302)  # Redirect
        self.send_header('Location', '/articles')
        self.end_headers()

print(f"Starting blog server at http://localhost:{PORT}")
print("Available routes:")
print("  • http://localhost:8000/articles")
print("  • http://localhost:8000/articles/create")
print("  • http://localhost:8000/articles/1/edit")

with socketserver.TCPServer(("", PORT), BlogHandler) as httpd:
    print(f"Server running on port {PORT}...")
    print("Press Ctrl+C to stop")
    httpd.serve_forever()
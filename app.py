from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS articles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# ===== WEB ROUTES =====
@app.route('/')
@app.route('/articles')
def articles():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY created_at DESC")
    articles_list = c.fetchall()
    conn.close()
    
    # Simple HTML if templates folder doesn't exist
    if not articles_list:
        return '''
        <h1>My Blog</h1>
        <p>No articles yet. <a href="/articles/create">Create first article</a></p>
        <p><a href="/api/articles">View API</a></p>
        '''
    
    html = '<h1>My Blog</h1>'
    html += '<a href="/articles/create">Create New Article</a> | '
    html += '<a href="/api/articles">API</a><hr>'
    
    for article in articles_list:
        html += f'''
        <div style="border:1px solid #ddd; padding:10px; margin:10px 0;">
            <h3>{article[1]}</h3>
            <p>{article[2][:100]}...</p>
            <small>{article[3]}</small><br>
            <a href="/articles/{article[0]}/edit">Edit</a>
        </div>
        '''
    
    return html

@app.route('/articles/create', methods=['GET', 'POST'])
def create_article():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        conn = sqlite3.connect('blog.db')
        c = conn.cursor()
        c.execute("INSERT INTO articles (title, content, created_at) VALUES (?, ?, ?)",
                  (title, content, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        conn.close()
        
        return redirect('/articles')
    
    return '''
    <h1>Create Article</h1>
    <form method="POST">
        <input type="text" name="title" placeholder="Title" required><br><br>
        <textarea name="content" rows="10" placeholder="Content" required></textarea><br><br>
        <button type="submit">Save</button>
        <a href="/articles">Cancel</a>
    </form>
    '''

@app.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
def edit_article(id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        
        c.execute("UPDATE articles SET title=?, content=? WHERE id=?", 
                  (title, content, id))
        conn.commit()
        conn.close()
        return redirect('/articles')
    
    c.execute("SELECT * FROM articles WHERE id=?", (id,))
    article = c.fetchone()
    conn.close()
    
    if not article:
        return "Article not found", 404
    
    return f'''
    <h1>Edit Article</h1>
    <form method="POST">
        <input type="text" name="title" value="{article[1]}" required><br><br>
        <textarea name="content" rows="10" required>{article[2]}</textarea><br><br>
        <button type="submit">Update</button>
        <a href="/articles">Cancel</a>
    </form>
    '''

# ===== API ROUTES (BONUS) =====
@app.route('/api/articles', methods=['GET', 'POST'])
def api_articles():
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM articles ORDER BY created_at DESC")
        articles = c.fetchall()
        conn.close()
        
        articles_list = []
        for article in articles:
            articles_list.append({
                'id': article[0],
                'title': article[1],
                'content': article[2],
                'created_at': article[3]
            })
        
        return jsonify({
            'articles': articles_list,
            'count': len(articles_list)
        })
    
    elif request.method == 'POST':
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            conn.close()
            return jsonify({'error': 'Title and content required'}), 400
        
        c.execute("INSERT INTO articles (title, content, created_at) VALUES (?, ?, ?)",
                  (data['title'], data['content'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        conn.commit()
        article_id = c.lastrowid
        conn.close()
        
        return jsonify({
            'message': 'Article created',
            'id': article_id,
            'title': data['title']
        }), 201

@app.route('/api/articles/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def api_article(id):
    conn = sqlite3.connect('blog.db')
    c = conn.cursor()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM articles WHERE id=?", (id,))
        article = c.fetchone()
        conn.close()
        
        if not article:
            return jsonify({'error': 'Article not found'}), 404
        
        return jsonify({
            'id': article[0],
            'title': article[1],
            'content': article[2],
            'created_at': article[3]
        })
    
    elif request.method == 'PUT':
        data = request.json
        c.execute("SELECT * FROM articles WHERE id=?", (id,))
        article = c.fetchone()
        
        if not article:
            conn.close()
            return jsonify({'error': 'Article not found'}), 404
        
        title = data.get('title', article[1])
        content = data.get('content', article[2])
        
        c.execute("UPDATE articles SET title=?, content=? WHERE id=?", 
                  (title, content, id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'message': 'Article updated',
            'id': id,
            'title': title
        })
    
    elif request.method == 'DELETE':
        c.execute("DELETE FROM articles WHERE id=?", (id,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Article deleted'})

# ===== API DOCS =====
@app.route('/api')
def api_docs():
    return '''
    <h1>API Documentation</h1>
    <h3>Endpoints:</h3>
    <ul>
        <li><strong>GET</strong> <a href="/api/articles">/api/articles</a> - Get all articles</li>
        <li><strong>POST</strong> /api/articles - Create article (send JSON)</li>
        <li><strong>GET</strong> <a href="/api/articles/1">/api/articles/&lt;id&gt;</a> - Get single article</li>
        <li><strong>PUT</strong> /api/articles/&lt;id&gt; - Update article</li>
        <li><strong>DELETE</strong> /api/articles/&lt;id&gt; - Delete article</li>
    </ul>
    <hr>
    <a href="/articles">← Back to Blog</a>
    '''

if __name__ == '__main__':
    print("Starting Flask blog application...")
    print("Open: http://localhost:5000/articles")
    print("API: http://localhost:5000/api/articles")
    app.run(debug=True)  
'use client';

import "./style.css";
import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface Article {
  link: string;
  title: string;
  description: string;
  image: string | null;
}

interface NewsData {
  [key: string]: Article[];
}

const NewsComponent = () => {
  const [newsData, setNewsData] = useState<NewsData>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('Dashboard');
  const [graphData, setGraphData] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/categories')
      .then(response => response.json())
      .then(data => {
        setCategories(data);
        if (data.length > 0) {
          setSelectedCategory(data[0]);
        }
      })
      .catch(error => console.error('Error fetching categories:', error));
  }, []);

  useEffect(() => {
    if (selectedCategory !== 'Dashboard') {
      fetch('http://127.0.0.1:5000/api/news')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(data => {
          setNewsData(data);
          setLoading(false);
          console.log("Fetched news data:", data);
        })
        .catch(error => {
          setError(error.message);
          setLoading(false);
          console.error('Error fetching news:', error);
        });
    } else {
      fetch('http://127.0.0.1:5001/api/graph-data')
        .then(response => response.json())
        .then(data => {
          setGraphData(data);
          setLoading(false);
          console.log("Fetched graph data:", data);
        })
        .catch(error => {
          setError(error.message);
          setLoading(false);
          console.error('Error fetching graph data:', error);
        });
    }
  }, [selectedCategory]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  const renderDashboard = () => (
    <div className="dashboard">
      <h2>Dashboard</h2>
      <div id="graphs">
        {graphData.map((graph, index) => (
          <div key={index} className="graph-container">
            <h3>{graph.title}</h3>
            <Plot data={graph.data} layout={{ title: graph.title }} />
          </div>
        ))}
      </div>
    </div>
  );

  const renderNews = (category: string) => (
    <div className="news-container">
      {newsData[category]?.map((article, index) => (
        <div key={index} className="news-article">
          {article.image && <img src={article.image} alt={article.title} className="news-image" />}
          <div className="news-content">
            <h2 className="news-title">{article.title}</h2>
            <p className="news-description">{article.description}</p>
            <a href={article.link} target="_blank" rel="noopener noreferrer" className="news-url">{article.link}</a>
          </div>
        </div>
      ))}
    </div>
  );

  return (
    <div>
      <div className="header">
        <nav>
          <ul>
            <li><a href="#" onClick={() => setSelectedCategory('Dashboard')} className={selectedCategory === 'Dashboard' ? 'active' : ''}>Dashboard</a></li>
            {categories.map(category => (
              <li key={category}><a href="#" onClick={() => setSelectedCategory(category)} className={selectedCategory === category ? 'active' : ''}>{category}</a></li>
            ))}
          </ul>
        </nav>
      </div>
      <div className="container">
        {selectedCategory === 'Dashboard' ? renderDashboard() : renderNews(selectedCategory)}
      </div>
    </div>
  );
};

export default NewsComponent;

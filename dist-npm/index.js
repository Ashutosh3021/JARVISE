/**
 * JARVIS AI - Node.js SDK
 * 
 * This module provides a JavaScript/TypeScript interface to JARVIS
 * 
 * @example
 * const jarvis = require('jarvis-ai');
 * 
 * // Chat
 * const response = await jarvis.chat('Hello!');
 * 
 * // Get stats
 * const stats = await jarvis.getStats();
 */

const axios = require('axios');
const WebSocket = require('ws');

const DEFAULT_URL = process.env.JARVIS_URL || 'http://localhost:8000';

class JarvisClient {
  constructor(options = {}) {
    this.url = options.url || DEFAULT_URL;
    this.wsUrl = this.url.replace('http', 'ws') + '/ws/chat';
    this.client = axios.create({
      baseURL: this.url,
      timeout: 60000
    });
  }
  
  async chat(message, options = {}) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.wsUrl);
      let response = '';
      
      ws.on('open', () => {
        ws.send(JSON.stringify({ type: 'message', content: message }));
      });
      
      ws.on('message', (data) => {
        const msg = JSON.parse(data);
        if (msg.type === 'chunk') {
          response += msg.content || '';
          if (options.onChunk) {
            options.onChunk(msg.content);
          }
        } else if (msg.type === 'done') {
          ws.close();
        }
      });
      
      ws.on('close', () => resolve(response));
      ws.on('error', reject);
      
      // Timeout
      setTimeout(() => {
        ws.close();
        resolve(response);
      }, options.timeout || 60000);
    });
  }
  
  async getStats() {
    const response = await this.client.get('/api/stats/current');
    return response.data;
  }
  
  async getMemories(sessionId = 'default', limit = 50) {
    const response = await this.client.get('/api/memory', {
      params: { session_id: sessionId, limit }
    });
    return response.data;
  }
  
  async searchMemory(query, limit = 10) {
    const response = await this.client.get('/api/memory/search', {
      params: { q: query, limit }
    });
    return response.data;
  }
  
  async healthCheck() {
    try {
      await this.client.get('/health');
      return true;
    } catch {
      return false;
    }
  }
}

module.exports = { JarvisClient };

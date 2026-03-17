#!/usr/bin/env node

/**
 * JARVIS AI Assistant - Node.js CLI
 * 
 * Usage:
 *   jarvis shell           # Interactive mode
 *   jarvis chat "message" # Send message
 *   jarvis server start   # Start server
 *   jarvis web            # Open web UI
 */

const { spawn } = require('child_process');
const path = require('path');
const axios = require('axios');
const WebSocket = require('ws');
const inquirer = require('inquirer');
const chalk = require('chalk');
const ora = require('ora');

// Configuration
const DEFAULT_URL = process.env.JARVIS_URL || 'http://localhost:8000';
const WS_URL = DEFAULT_URL.replace('http', 'ws') + '/ws/chat';

// Colors
const colors = {
  primary: chalk.cyan,
  success: chalk.green,
  error: chalk.red,
  warning: chalk.yellow,
  info: chalk.blue
};

// Check if server is running
async function checkServer() {
  try {
    const response = await axios.get(DEFAULT_URL + '/health', { timeout: 2000 });
    return response.status === 200;
  } catch {
    return false;
  }
}

// Start server
async function startServer() {
  console.log(colors.primary('Starting JARVIS server...'));
  
  const serverProcess = spawn('python', ['main.py'], {
    cwd: path.join(__dirname, '..'),
    stdio: 'inherit',
    shell: true
  });
  
  return serverProcess;
}

// WebSocket chat
async function chat(message) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(WS_URL);
    let response = '';
    
    ws.on('open', () => {
      ws.send(JSON.stringify({ type: 'message', content: message }));
    });
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data);
      if (msg.type === 'chunk') {
        process.stdout.write(msg.content || '');
        response += msg.content || '';
      } else if (msg.type === 'done') {
        ws.close();
      }
    });
    
    ws.on('close', () => {
      resolve(response);
    });
    
    ws.on('error', (err) => {
      reject(err);
    });
    
    // Timeout
    setTimeout(() => {
      ws.close();
      resolve(response);
    }, 60000);
  });
}

// Get stats
async function getStats() {
  const response = await axios.get(DEFAULT_URL + '/api/stats/current');
  return response.data;
}

// Get memories
async function getMemories(limit = 10) {
  const response = await axios.get(DEFAULT_URL + '/api/memory', {
    params: { limit }
  });
  return response.data;
}

// Interactive shell
async function shell() {
  console.log(colors.primary(`
╔═══════════════════════════════════════════════════════════╗
║                    JARVIS Interactive Shell               ║
║                                                           ║
║  Commands:                                                ║
║    :help     - Show this help                            ║
║    :memory   - View memories                              ║
║    :stats    - Show system stats                          ║
║    :clear    - Clear conversation                        ║
║    :web      - Open web UI                               ║
║    :quit     - Exit shell                                ║
╚═══════════════════════════════════════════════════════════╝
  `));
  
  const spinner = ora('Connecting to JARVIS...').start();
  const serverRunning = await checkServer();
  spinner.stop();
  
  if (!serverRunning) {
    console.log(colors.warning('Server not running. Starting...'));
    await startServer();
    await new Promise(r => setTimeout(r, 5000));
  }
  
  console.log(colors.success('✓ Connected to JARVIS\n'));
  
  // Interactive loop
  while (true) {
    try {
      const { input } = await inquirer.prompt([{
        type: 'input',
        name: 'input',
        message: chalk.green('[You]'),
        prefix: ''
      }]);
      
      if (!input.trim()) continue;
      
      // Handle commands
      if (input.startsWith(':')) {
        const cmd = input.slice(1).trim().toLowerCase();
        
        if (cmd === 'help') {
          console.log(`
Commands:
  :help     - Show this help
  :memory   - View recent memories  
  :stats    - Show system statistics
  :clear    - Clear conversation history
  :web      - Open web UI
  :quit     - Exit shell
          `);
        } else if (cmd === 'stats') {
          const stats = await getStats();
          console.log(`
System Statistics:
  CPU:     ${stats.cpu?.percent || 'N/A'}%
  Memory:  ${stats.memory?.used_gb || 'N/A'}GB / ${stats.memory?.total_gb || 'N/A'}GB
          `);
        } else if (cmd === 'memory' || cmd === 'memories') {
          const memories = await getMemories(10);
          console.log(`\n--- Recent Memories (${memories.count || 0}) ---`);
          (memories.memories || []).forEach((m, i) => {
            console.log(`${i+1}. ${(m.query || '').substring(0, 60)}`);
          });
          console.log();
        } else if (cmd === 'quit' || cmd === 'exit') {
          console.log(colors.primary('\nGoodbye!'));
          break;
        } else if (cmd === 'web') {
          const { default: open } = await import('open');
          open(DEFAULT_URL);
        } else {
          console.log(colors.warning(`Unknown command: ${cmd}`));
        }
        continue;
      }
      
      // Chat
      process.stdout.write(chalk.cyan('\n[JARVIS] '));
      await chat(input);
      console.log('\n');
      
    } catch (err) {
      console.log(colors.error(`\nError: ${err.message}`));
    }
  }
}

// Main CLI
async function main() {
  const args = process.argv.slice(2);
  const command = args[0];
  
  if (!command) {
    console.log(colors.primary(`
╔═══════════════════════════════════════════════════════════╗
║                    JARVIS AI Assistant                    ║
║                    Version 1.0.0                           ║
╚═══════════════════════════════════════════════════════════╝

Usage:
  jarvis shell           # Interactive shell mode
  jarvis chat "message" # Send a message
  jarvis server start   # Start server
  jarvis web            # Open web UI
  jarvis stats          # Show system stats

For more info: jarvis --help
    `));
    return;
  }
  
  try {
    switch (command) {
      case 'shell':
      case 's':
        await shell();
        break;
        
      case 'chat':
      case 'c':
        const message = args.slice(1).join(' ');
        if (!message) {
          console.log(colors.error('Please provide a message'));
          process.exit(1);
        }
        console.log(colors.green(`[You] ${message}\n`));
        process.stdout.write(colors.cyan('[JARVIS] '));
        await chat(message);
        console.log('\n');
        break;
        
      case 'server':
        const serverCmd = args[1];
        if (serverCmd === 'start') {
          await startServer();
        } else {
          console.log('Usage: jarvis server start');
        }
        break;
        
      case 'web':
      case 'w':
        const { default: open } = await import('open');
        const running = await checkServer();
        if (!running) {
          console.log(colors.warning('Starting server...'));
          startServer();
          await new Promise(r => setTimeout(r, 5000));
        }
        open(DEFAULT_URL);
        console.log(colors.success(`Opening ${DEFAULT_URL}`));
        break;
        
      case 'stats':
        const stats = await getStats();
        console.log(`
System Statistics:
  CPU:     ${stats.cpu?.percent || 'N/A'}%
  Memory:  ${stats.memory?.used_gb || 'N/A'}GB / ${stats.memory?.total_gb || 'N/A'}GB
        `);
        break;
        
      default:
        console.log(colors.error(`Unknown command: ${command}`));
        console.log('Run jarvis --help for usage');
    }
  } catch (err) {
    console.log(colors.error(`Error: ${err.message}`));
    process.exit(1);
  }
}

main();

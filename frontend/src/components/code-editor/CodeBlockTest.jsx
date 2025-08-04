import React from 'react'
import ReadOnlyCodeBlock from './ReadOnlyCodeBlock'

/**
 * Test component to demonstrate CodeMirror 6 integration
 * This shows how different languages are rendered
 */
export default function CodeBlockTest() {
  const pythonCode = `def fibonacci(n):
    """Calculate the nth Fibonacci number recursively."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Generate first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")`

  const javascriptCode = `function fibonacci(n) {
    // Calculate the nth Fibonacci number recursively
    if (n <= 1) {
        return n;
    }
    return fibonacci(n-1) + fibonacci(n-2);
}

// Generate first 10 Fibonacci numbers
for (let i = 0; i < 10; i++) {
    console.log(\`F(\${i}) = \${fibonacci(i)}\`);
}`

  const javaCode = `public class Fibonacci {
    /**
     * Calculate the nth Fibonacci number recursively
     */
    public static long fibonacci(int n) {
        if (n <= 1) {
            return n;
        }
        return fibonacci(n-1) + fibonacci(n-2);
    }
    
    public static void main(String[] args) {
        // Generate first 10 Fibonacci numbers
        for (int i = 0; i < 10; i++) {
            System.out.println("F(" + i + ") = " + fibonacci(i));
        }
    }
}`

  const cppCode = `#include <iostream>
using namespace std;

/**
 * Calculate the nth Fibonacci number recursively
 */
long fibonacci(int n) {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n-1) + fibonacci(n-2);
}

int main() {
    // Generate first 10 Fibonacci numbers
    for (int i = 0; i < 10; i++) {
        cout << "F(" << i << ") = " << fibonacci(i) << endl;
    }
    return 0;
}`

  const htmlCode = `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fibonacci Calculator</title>
</head>
<body>
    <h1>Fibonacci Calculator</h1>
    <input type="number" id="numberInput" placeholder="Enter a number">
    <button onclick="calculateFibonacci()">Calculate</button>
    <p id="result"></p>
    
    <script>
        function calculateFibonacci() {
            const n = parseInt(document.getElementById('numberInput').value);
            const result = fibonacci(n);
            document.getElementById('result').textContent = \`F(\${n}) = \${result}\`;
        }
    </script>
</body>
</html>`

  const cssCode = `.fibonacci-calculator {
    max-width: 600px;
    margin: 0 auto;
    padding: 2rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.fibonacci-calculator h1 {
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.input-group {
    display: flex;
    gap: 1rem;
    margin-bottom: 1rem;
}

.input-group input {
    flex: 1;
    padding: 0.75rem;
    border: none;
    border-radius: 6px;
    font-size: 1rem;
}

.input-group button {
    padding: 0.75rem 1.5rem;
    background: #4CAF50;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.3s ease;
}

.input-group button:hover {
    background: #45a049;
}`

  return (
    <div className="space-y-8 p-6">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">
        CodeMirror 6 Integration Test
      </h1>
      
      <div className="space-y-6">
        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            Python Code
          </h2>
          <ReadOnlyCodeBlock code={pythonCode} language="python" />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            JavaScript Code
          </h2>
          <ReadOnlyCodeBlock code={javascriptCode} language="javascript" />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            Java Code
          </h2>
          <ReadOnlyCodeBlock code={javaCode} language="java" />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            C++ Code
          </h2>
          <ReadOnlyCodeBlock code={cppCode} language="cpp" />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            HTML Code
          </h2>
          <ReadOnlyCodeBlock code={htmlCode} language="html" />
        </div>

        <div>
          <h2 className="text-xl font-semibold mb-3 text-gray-900 dark:text-gray-100">
            CSS Code
          </h2>
          <ReadOnlyCodeBlock code={cssCode} language="css" />
        </div>
      </div>
    </div>
  )
}
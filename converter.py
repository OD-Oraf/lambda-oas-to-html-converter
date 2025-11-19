"""
OAS to HTML Converter
Simplified converter that takes OAS content and returns HTML
"""

import subprocess
import os
import tempfile
import time
import shutil
from typing import Dict, Optional


class OASConverter:
    """Convert OAS content to HTML using swagger-ui-offline-packager"""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.node_path = None
        self.node_modules_path = None
        self.cli_path = None
        self.env = None
        self._setup_environment()
    
    def _log(self, message: str):
        """Print log message if verbose mode is enabled"""
        if self.verbose:
            print(message)
    
    def _setup_environment(self):
        """Setup Node.js and npm environment"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Check if running in Lambda (Lambda layers are at /opt)
        lambda_nodejs_path = '/opt/nodejs'
        lambda_node_binary = '/opt/nodejs/bin/node'
        local_nodejs_dir = os.path.join(script_dir, 'nodejs')
        
        # Priority 1: Lambda layer (if exists)
        if os.path.exists(lambda_nodejs_path):
            self._log("🔍 Detected Lambda environment")
            self.node_modules_path = os.path.join(lambda_nodejs_path, 'node_modules')
            
            # Check for Node.js binary in Lambda layer
            if os.path.exists(lambda_node_binary):
                self.node_path = lambda_node_binary
                self._log(f"✓ Using Lambda layer Node.js: {self.node_path}")
            else:
                # Use system node in Lambda runtime
                system_node = shutil.which('node')
                if system_node:
                    self.node_path = system_node
                    self._log(f"✓ Using Lambda runtime Node.js: {self.node_path}")
                else:
                    raise FileNotFoundError("Node.js not found in Lambda layer or runtime")
        
        # Priority 2: Local nodejs directory
        elif os.path.exists(local_nodejs_dir):
            self._log("🔍 Detected local environment")
            self.node_modules_path = os.path.join(local_nodejs_dir, 'node_modules')
            
            # Try system Node.js first
            system_node = shutil.which('node')
            if system_node:
                self.node_path = system_node
                self._log(f"✓ Using system Node.js: {self.node_path}")
            else:
                # Fallback to local nodejs/bin/node
                self.node_path = os.path.join(local_nodejs_dir, 'bin/node')
                if os.path.exists(self.node_path):
                    self._log(f"✓ Using local Node.js: {self.node_path}")
                else:
                    raise FileNotFoundError(f"Node.js not found at: {self.node_path}")
        
        else:
            raise FileNotFoundError(
                "Node.js environment not found. "
                "Expected either /opt/nodejs (Lambda) or local nodejs/ directory"
            )
        
        # Setup Node.js bin directory
        self.nodejs_bin = os.path.dirname(self.node_path)
        
        # Verify CLI exists
        self.cli_path = os.path.join(self.node_modules_path, 'swagger-ui-offline-packager/bin/cli.js')
        if not os.path.exists(self.cli_path):
            raise FileNotFoundError(
                f"swagger-ui-offline-packager not found at: {self.cli_path}\n"
                f"Make sure Node.js layer includes swagger-ui-offline-packager"
            )
        
        # Setup environment variables
        self.env = os.environ.copy()
        self.env['PATH'] = f'{self.nodejs_bin}:' + self.env.get('PATH', '')
        self.env['NODE_PATH'] = self.node_modules_path
        
        self._log(f"✓ Node modules: {self.node_modules_path}")
        self._log(f"✓ CLI path: {self.cli_path}")
    
    def convert(self, oas_content: str, filename: str = "openapi.json", timeout: int = 60) -> Dict[str, any]:
        """
        Convert OAS content to HTML
        
        Args:
            oas_content: OAS specification as string (JSON or YAML)
            filename: Name for the OAS file (used for temp file)
            timeout: Subprocess timeout in seconds
        
        Returns:
            Dictionary with:
            - success: bool
            - html_content: str (HTML content)
            - html_file: str (path to temp HTML file)
            - duration: float (conversion time in seconds)
            - error: str (if failed)
        """
        start_time = time.time()
        
        self._log(f"\n{'='*80}")
        self._log(f"🔄 Converting OAS to HTML")
        self._log(f"{'='*80}")
        self._log(f"Filename: {filename}")
        self._log(f"Content Size: {len(oas_content)} bytes ({len(oas_content) / 1024:.2f} KB)")
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='oas_converter_')
        
        try:
            # Write OAS content to temp file
            oas_file_path = os.path.join(temp_dir, filename)
            with open(oas_file_path, 'w') as f:
                f.write(oas_content)
            
            self._log(f"✓ Written to temp file: {oas_file_path}")
            
            # Output HTML file path
            html_output = os.path.join(temp_dir, 'index.html')
            
            # Run conversion
            self._log(f"\n⚙️  Running swagger-ui-offline-packager...")
            self._log(f"Timeout: {timeout}s")
            
            try:
                result = subprocess.run(
                    [
                        self.node_path,
                        self.cli_path,
                        oas_file_path,
                        html_output
                    ],
                    capture_output=True,
                    text=True,
                    env=self.env,
                    timeout=timeout
                )
                
                elapsed = time.time() - start_time
                
                if result.returncode != 0:
                    error = f"Conversion failed with return code {result.returncode}"
                    self._log(f"\n❌ {error}")
                    self._log(f"Stderr: {result.stderr[:500]}")
                    return {
                        'success': False,
                        'error': error,
                        'stderr': result.stderr,
                        'stdout': result.stdout,
                        'duration': elapsed
                    }
                
                # Verify output file was created
                if not os.path.exists(html_output):
                    error = "Output HTML file was not created"
                    self._log(f"❌ {error}")
                    return {
                        'success': False,
                        'error': error,
                        'duration': elapsed
                    }
                
                # Read HTML content
                with open(html_output, 'r') as f:
                    html_content = f.read()
                
                output_size = len(html_content)
                
                self._log(f"\n{'='*80}")
                self._log(f"✅ Conversion Successful")
                self._log(f"{'='*80}")
                self._log(f"Output Size: {output_size} bytes ({output_size / 1024:.2f} KB, {output_size / 1024 / 1024:.2f} MB)")
                self._log(f"Duration: {elapsed:.2f}s")
                self._log(f"{'='*80}\n")
                
                return {
                    'success': True,
                    'html_content': html_content,
                    'html_file': html_output,
                    'output_size': output_size,
                    'duration': elapsed
                }
                
            except subprocess.TimeoutExpired:
                elapsed = time.time() - start_time
                error = f"Conversion timed out after {timeout} seconds"
                self._log(f"\n❌ {error}")
                return {
                    'success': False,
                    'error': error,
                    'duration': elapsed
                }
        
        except Exception as e:
            elapsed = time.time() - start_time
            error = f"Conversion failed: {str(e)}"
            self._log(f"\n❌ {error}")
            return {
                'success': False,
                'error': error,
                'duration': elapsed
            }
        
        finally:
            # Note: We don't cleanup temp_dir here so the HTML file can be accessed
            # Caller should cleanup if needed, or rely on OS to cleanup /tmp
            pass


def convert_oas(oas_content: str, filename: str = "openapi.json", verbose: bool = True) -> Dict[str, any]:
    """
    Convenience function to convert OAS content to HTML
    
    Args:
        oas_content: OAS specification as string
        filename: Name for the OAS file
        verbose: Enable verbose logging
    
    Returns:
        Dictionary with conversion results
    """
    converter = OASConverter(verbose=verbose)
    return converter.convert(oas_content, filename)


if __name__ == '__main__':
    # Test converter
    test_oas = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /test:
    get:
      summary: Test endpoint
      responses:
        '200':
          description: OK
"""
    
    result = convert_oas(test_oas, "test-api.yaml")
    
    if result['success']:
        print(f"\n✅ Conversion successful!")
        print(f"Duration: {result['duration']:.2f}s")
        print(f"HTML file: {result['html_file']}")
    else:
        print(f"\n❌ Conversion failed: {result['error']}")

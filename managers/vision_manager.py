import os
import subprocess
import asyncio
from utils.logger import Logger

class VisionManager:
    """Manager class for repository visualization using repo-visualizer."""
    
    def __init__(self, model=None):
        """Initialize the vision manager."""
        self.logger = Logger(model=model)
        self.model = model

    async def generate_visualization(self):
        """
        Generate repository visualization using repo-visualizer.
        
        Raises:
            RuntimeError: If Node.js is not installed
            subprocess.CalledProcessError: If visualization generation fails
        """
        try:
            # Validate Node.js installation quietly
            try:
                process = await asyncio.create_subprocess_exec(
                    'node', '--version',
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL
                )
                await process.wait()
            except FileNotFoundError:
                raise RuntimeError(
                    "Node.js not found! Please install Node.js from https://nodejs.org/"
                )

            # Get repo-visualizer path
            repo_visualizer_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vendor', 'repo-visualizer')
            dist_path = os.path.join(repo_visualizer_path, 'dist', 'index.js')

            if not os.path.exists(dist_path):
                self.logger.info("🔨 repo-visualizer needs to be built. Attempting build...")
                
                try:
                    # Install dependencies first
                    process = await asyncio.create_subprocess_exec(
                        'npm', 'install',
                        cwd=repo_visualizer_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        self.logger.error("❌ npm install failed. Trying with --force...")
                        # Clear npm cache and retry with force
                        await asyncio.create_subprocess_exec('npm', 'cache', 'clean', '--force')
                        process = await asyncio.create_subprocess_exec(
                            'npm', 'install', '--force',
                            cwd=repo_visualizer_path,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode != 0:
                            raise RuntimeError(
                                f"Failed to install dependencies:\n"
                                f"stdout: {stdout.decode()}\n"
                                f"stderr: {stderr.decode()}"
                            )
                    
                    # Run build
                    self.logger.info("📦 Building repo-visualizer...")
                    process = await asyncio.create_subprocess_exec(
                        'npm', 'run', 'build',
                        cwd=repo_visualizer_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        raise RuntimeError(
                            f"Build failed:\n"
                            f"stdout: {stdout.decode()}\n"
                            f"stderr: {stderr.decode()}\n"
                            f"\nTry these steps manually:\n"
                            f"1. cd {repo_visualizer_path}\n"
                            f"2. npm cache clean --force\n"
                            f"3. rm -rf node_modules package-lock.json\n"
                            f"4. npm install --force\n"
                            f"5. npm run build"
                        )
                        
                    self.logger.success("✨ repo-visualizer built successfully")
                    
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to build repo-visualizer. Please build manually:\n"
                        f"1. cd {repo_visualizer_path}\n"
                        f"2. npm install\n"
                        f"3. npm run build\n"
                        f"\nError: {str(e)}"
                    )

            # Run visualization with minimal options
            self.logger.debug("🎨 Generating repository visualization...")
            process = await asyncio.create_subprocess_exec(
                'node',
                dist_path,
                '--verbose',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                self.logger.error(f"Visualization command failed with return code {process.returncode}")
                if stdout:
                    self.logger.error(f"stdout: {stdout.decode()}")
                if stderr:
                    self.logger.error(f"stderr: {stderr.decode()}")
                raise subprocess.CalledProcessError(
                    process.returncode,
                    f"node {dist_path} --verbose",
                    output=stdout,
                    stderr=stderr
                )

            self.logger.debug("✨ Repository visualization SVG generated successfully")

            # Convert SVG to PNG
            try:
                from cairosvg import svg2png
                
                # Read the SVG
                with open('./diagram.svg', 'rb') as svg_file:
                    svg_data = svg_file.read()
                    
                # Convert and save as PNG
                svg2png(bytestring=svg_data,
                       write_to='./diagram.png',
                       output_width=1024,
                       output_height=1024)
                
                self.logger.debug("✨ Repository visualization PNG generated successfully")
                
            except ImportError:
                self.logger.error("❌ cairosvg not installed. Please install with: pip install cairosvg")
                raise
            except Exception as e:
                self.logger.error(f"Failed to convert SVG to PNG: {str(e)}")
                raise

        except Exception as e:
            self.logger.error(f"Failed to generate visualization: {str(e)}")
            raise


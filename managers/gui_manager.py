import os
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QSlider, QScrollArea,
                            QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QIcon
from utils.logger import Logger
from managers.agents_manager import AgentsManager
from managers.vision_manager import VisionManager
from PIL import Image, ImageDraw

class GUIManager:
    """Manager class for the KinOS GUI."""
    
    def __init__(self, model=None):
        """Initialize the GUI manager."""
        self.logger = Logger(model=model)
        self.model = model
        self.agents_manager = AgentsManager(model=model)
        self.vision_manager = VisionManager(model=model)
        self.app = None
        self.window = None
        
    async def start_gui(self):
        """Start the GUI application."""
        try:
            self.logger.info("Starting KinOS GUI...")
            
            # Check if we're already running
            if self.app is not None:
                self.logger.warning("GUI already running")
                return
                
            # Create Qt application with proper args
            import sys
            self.app = QApplication(sys.argv)
            self.logger.info("Created QApplication")
            
            # Set application name and organization
            self.app.setApplicationName("KinOS")
            self.app.setOrganizationName("KinOS")
            self.logger.info("Set application info")
            
            # Create main window
            try:
                self.window = MainWindow(self)
                self.logger.info("Created MainWindow")
            except Exception as e:
                self.logger.error(f"Failed to create main window: {str(e)}")
                raise
            
            # Show window
            try:
                self.window.show()
                self.logger.info("Window shown")
            except Exception as e:
                self.logger.error(f"Failed to show window: {str(e)}")
                raise
            
            # Initialize event loop
            try:
                import qasync
                loop = qasync.QEventLoop(self.app)
                asyncio.set_event_loop(loop)
                self.logger.info("Event loop created")
            except Exception as e:
                self.logger.error(f"Failed to create event loop: {str(e)}")
                raise
            
            # Start update timers
            try:
                self._start_update_timers()
                self.logger.info("Started update timers")
            except Exception as e:
                self.logger.error(f"Failed to start timers: {str(e)}")
                raise
            
            # Run event loop
            self.logger.info("Starting event loop...")
            await loop.run_forever()
            
        except Exception as e:
            self.logger.error(f"GUI startup failed: {str(e)}")
            import traceback
            self.logger.error(f"Traceback:\n{traceback.format_exc()}")
            raise
        finally:
            # Cleanup
            if self.app:
                self.app.quit()

    def _start_update_timers(self):
        """Start timers for periodic updates."""
        # Update agent status every 5 seconds
        self.agent_timer = QTimer()
        self.agent_timer.timeout.connect(self.window.update_agents)
        self.agent_timer.start(5000)
        
        # Update diagram every 30 seconds
        self.diagram_timer = QTimer()
        self.diagram_timer.timeout.connect(self.window.update_diagram)
        self.diagram_timer.start(30000)
        
        # Update activity feeds every 2 seconds
        self.activity_timer = QTimer()
        self.activity_timer.timeout.connect(self.window._update_activity_feed)
        self.activity_timer.timeout.connect(self.window._update_commit_history)
        self.activity_timer.start(2000)

    def cleanup(self):
        """Clean up GUI resources."""
        try:
            if hasattr(self, 'agent_timer'):
                self.agent_timer.stop()
            if hasattr(self, 'diagram_timer'):
                self.diagram_timer.stop()
            if hasattr(self, 'activity_timer'):
                self.activity_timer.stop()
            if self.window:
                self.window.close()
            if self.app:
                self.app.quit()
        except Exception as e:
            self.logger.error(f"Cleanup failed: {str(e)}")

    def generate_agent_avatar(self, agent_name):
        """Generate a unique avatar for an agent."""
        try:
            # Create a 128x128 image with unique pattern based on agent name
            img = Image.new('RGB', (128, 128), color='white')
            d = ImageDraw.Draw(img)
            
            # Use agent name to generate unique pattern
            hash_val = hash(agent_name)
            
            # Draw some shapes based on hash
            for i in range(8):
                x1 = ((hash_val + i*37) % 128)
                y1 = ((hash_val + i*73) % 128)
                x2 = ((hash_val + i*89) % 128)
                y2 = ((hash_val + i*127) % 128)
                color = (
                    (hash_val + i*33) % 256,
                    (hash_val + i*71) % 256,
                    (hash_val + i*113) % 256
                )
                d.rectangle([x1, y1, x2, y2], fill=color)
            
            # Save to temp file
            avatar_path = f".aider.avatar.{agent_name}.png"
            img.save(avatar_path)
            return avatar_path
            
        except Exception as e:
            self.logger.error(f"Avatar generation failed: {str(e)}")
            return None

class FileEditor(QWidget):
    """File editor widget with syntax highlighting."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """Initialize the editor UI."""
        layout = QVBoxLayout(self)
        
        # Add toolbar
        toolbar = QHBoxLayout()
        
        # Save button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(self.save_btn)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.close)
        toolbar.addWidget(self.cancel_btn)
        
        layout.addLayout(toolbar)
        
        # Add text editor
        self.editor = QTextEdit()
        layout.addWidget(self.editor)
        
    def load_file(self, filepath):
        """Load file content into editor."""
        self.current_file = filepath
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.editor.setPlainText(content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load file: {str(e)}")
            
    def _save_file(self):
        """Save current content to file."""
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            QMessageBox.information(self, "Success", "File saved successfully")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not save file: {str(e)}")

class MainWindow(QMainWindow):
    """Main window for the KinOS GUI."""
    
    def __init__(self, manager):
        super().__init__()
        self.manager = manager
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle('KinOS')
        self.setMinimumSize(1024, 768)
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QHBoxLayout(main_widget)
        
        # Add agent roster (left panel)
        self.agent_scroll = QScrollArea()
        self.agent_widget = QWidget()
        self.agent_layout = QVBoxLayout(self.agent_widget)
        self.agent_scroll.setWidget(self.agent_widget)
        self.agent_scroll.setWidgetResizable(True)
        layout.addWidget(self.agent_scroll, stretch=1)
        
        # Add main content area
        content_layout = QVBoxLayout()
        
        # Add control panel
        controls = self._create_control_panel()
        content_layout.addWidget(controls)
        
        # Add diagram view
        self.diagram_label = QLabel()
        self.diagram_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.diagram_label, stretch=3)
        
        layout.addLayout(content_layout, stretch=2)
        
        # Add activity feed (right panel)
        activity_layout = QVBoxLayout()
        
        # Add commit history
        commit_label = QLabel("Recent Commits")
        self.commit_widget = QWidget()
        self.commit_layout = QVBoxLayout(self.commit_widget)
        activity_layout.addWidget(commit_label)
        activity_layout.addWidget(self.commit_widget, stretch=1)
        
        # Add suivi log
        suivi_label = QLabel("Activity Log")
        self.suivi_widget = QWidget()
        self.suivi_layout = QVBoxLayout(self.suivi_widget)
        activity_layout.addWidget(suivi_label)
        activity_layout.addWidget(self.suivi_widget, stretch=1)
        
        layout.addLayout(activity_layout, stretch=1)
        
        # Initial updates
        self.update_agents()
        self.update_diagram()
        
    def _create_control_panel(self):
        """Create the control panel widget."""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        
        # Mission controls
        mission_btn = QPushButton("Edit Mission")
        mission_btn.clicked.connect(self._edit_mission)
        layout.addWidget(mission_btn)
        
        todo_btn = QPushButton("Edit Todolist")
        todo_btn.clicked.connect(self._edit_todolist)
        layout.addWidget(todo_btn)
        
        # Agent controls
        self.start_btn = QPushButton("Start Agents")
        self.start_btn.clicked.connect(self._toggle_agents)
        layout.addWidget(self.start_btn)
        
        self.agent_slider = QSlider(Qt.Orientation.Horizontal)
        self.agent_slider.setMinimum(1)
        self.agent_slider.setMaximum(10)
        self.agent_slider.setValue(3)
        layout.addWidget(self.agent_slider)
        
        return panel
        
    def update_agents(self):
        """Update the agent roster display."""
        # Clear existing agents
        while self.agent_layout.count():
            child = self.agent_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
                
        # Get current agents
        agents = self.manager.agents_manager._get_available_agents()
        
        # Add agent cards
        for agent in agents:
            card = QWidget()
            card_layout = QHBoxLayout(card)
            
            # Add avatar
            avatar_path = self.manager.generate_agent_avatar(agent)
            if avatar_path and os.path.exists(avatar_path):
                avatar_label = QLabel()
                pixmap = QPixmap(avatar_path)
                avatar_label.setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio))
                card_layout.addWidget(avatar_label)
            
            # Add agent info
            info_layout = QVBoxLayout()
            name_label = QLabel(agent)
            info_layout.addWidget(name_label)
            
            # Get last message from objective file
            objective_path = f".aider.objective.{agent}.md"
            if os.path.exists(objective_path):
                try:
                    with open(objective_path, 'r', encoding='utf-8') as f:
                        last_msg = f.read().split('\n')[0]  # Get first line
                        msg_label = QLabel(last_msg)
                        msg_label.setWordWrap(True)
                        info_layout.addWidget(msg_label)
                except Exception as e:
                    self.manager.logger.warning(f"Could not read objective for {agent}: {str(e)}")
            
            card_layout.addLayout(info_layout)
            self.agent_layout.addWidget(card)
            
    def _update_activity_feed(self):
        """Update the activity feed from suivi.md."""
        try:
            # Clear existing items
            while self.suivi_layout.count():
                child = self.suivi_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            # Read last 10 lines from suivi.md
            if os.path.exists('suivi.md'):
                with open('suivi.md', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    last_lines = lines[-10:] if len(lines) > 10 else lines
                    
                # Add each line as a label
                for line in reversed(last_lines):
                    label = QLabel(line.strip())
                    label.setWordWrap(True)
                    self.suivi_layout.addWidget(label)
                    
        except Exception as e:
            self.manager.logger.error(f"Failed to update activity feed: {str(e)}")

    def _update_commit_history(self):
        """Update the commit history display."""
        try:
            # Clear existing items
            while self.commit_layout.count():
                child = self.commit_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()
                    
            # Get recent commits
            import subprocess
            result = subprocess.run(
                ['git', 'log', '-5', '--pretty=format:%h - %s'],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                commits = result.stdout.split('\n')
                for commit in commits:
                    if commit.strip():
                        label = QLabel(commit.strip())
                        label.setWordWrap(True)
                        self.commit_layout.addWidget(label)
                    
        except Exception as e:
            self.manager.logger.error(f"Failed to update commit history: {str(e)}")

    def update_diagram(self):
        """Update the repository diagram display."""
        try:
            if os.path.exists('./diagram.png'):
                pixmap = QPixmap('./diagram.png')
                scaled = pixmap.scaled(
                    self.diagram_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.diagram_label.setPixmap(scaled)
        except Exception as e:
            self.manager.logger.error(f"Failed to update diagram: {str(e)}")
            
    def _edit_mission(self):
        """Open mission file for editing."""
        try:
            editor = FileEditor()
            editor.load_file('.aider.mission.md')
            editor.show()
        except Exception as e:
            self.manager.logger.error(f"Could not open mission editor: {str(e)}")
        
    def _edit_todolist(self):
        """Open todolist file for editing."""
        try:
            editor = FileEditor()
            editor.load_file('todolist.md')
            editor.show()
        except Exception as e:
            self.manager.logger.error(f"Could not open todolist editor: {str(e)}")
        
    def _toggle_agents(self):
        """Toggle agent execution."""
        # TODO: Implement agent control
        pass

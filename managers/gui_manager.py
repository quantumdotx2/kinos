import os
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QPushButton, QSlider, QScrollArea)
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
            # Create Qt application
            self.app = QApplication([])
            self.window = MainWindow(self)
            self.window.show()
            
            # Start event loop
            import qasync
            loop = qasync.QEventLoop(self.app)
            asyncio.set_event_loop(loop)
            
            # Run periodic updates
            self._start_update_timers()
            
            # Run event loop
            await loop.run_forever()
            
        except Exception as e:
            self.logger.error(f"GUI startup failed: {str(e)}")
            raise

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
        # TODO: Implement file editor
        pass
        
    def _edit_todolist(self):
        """Open todolist file for editing."""
        # TODO: Implement file editor
        pass
        
    def _toggle_agents(self):
        """Toggle agent execution."""
        # TODO: Implement agent control
        pass

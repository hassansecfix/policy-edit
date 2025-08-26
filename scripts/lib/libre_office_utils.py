"""
LibreOffice Utilities - Connection, Setup, and Document Operations

This module provides utilities for working with LibreOffice in headless mode,
including connection management, document operations, and UNO bridge helpers.
"""

import os
import sys
import time
import subprocess
import socket
from pathlib import Path
from typing import Optional, Tuple, Any


class LibreOfficeManager:
    """
    Manages LibreOffice headless operations and document manipulation.
    """
    
    def __init__(self, fast_mode: bool = False):
        """Initialize LibreOffice manager."""
        self.fast_mode = fast_mode
        self.ctx = None
        self.desktop = None
        self.smgr = None
        
    def ensure_listener(self) -> None:
        """
        Start a headless LibreOffice UNO listener on port 2002 if not already running.
        """
        try:
            # Kill any existing LibreOffice processes to ensure clean start
            subprocess.run(["pkill", "-f", "soffice"], capture_output=True, 
                         timeout=2 if self.fast_mode else 5)
            time.sleep(0.5 if self.fast_mode else 1)
            
            # Create a temporary user profile with correct author info
            profile_dir = "/tmp/lo_profile_secfix"
            if not self.fast_mode:
                self._create_user_profile(profile_dir)
            
            # Set environment variables for LibreOffice user info
            os.environ['LO_USER_GIVENNAME'] = 'Secfix'
            os.environ['LO_USER_SURNAME'] = 'AI'
            
            # Start LibreOffice headless listener
            self._start_headless_listener(profile_dir)
            
            # Wait and test connection
            self._wait_for_connection()
            
        except FileNotFoundError:
            print("ERROR: 'soffice' not found on PATH. Install LibreOffice or add it to PATH.", 
                  file=sys.stderr)
    
    def _create_user_profile(self, profile_dir: str) -> None:
        """Create LibreOffice user profile with Secfix AI author info."""
        try:
            import shutil
            if os.path.exists(profile_dir):
                shutil.rmtree(profile_dir)
            os.makedirs(profile_dir, exist_ok=True)
            
            # Create a registrymodifications.xcu file to set user info
            registry_content = '''<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <item oor:path="/org.openoffice.UserProfile/Data">
    <prop oor:name="givenname" oor:op="fuse">
      <value>Secfix</value>
    </prop>
    <prop oor:name="sn" oor:op="fuse">
      <value>AI</value>
    </prop>
  </item>
</oor:items>'''
            with open(f"{profile_dir}/registrymodifications.xcu", "w") as f:
                f.write(registry_content)
            print("✅ Created LibreOffice profile with Secfix AI author")
        except Exception as e:
            print(f"Could not create profile: {e}")
    
    def _start_headless_listener(self, profile_dir: str) -> None:
        """Start LibreOffice headless listener process."""
        subprocess.Popen([
            "soffice",
            "--headless",
            "--nologo",
            "--nodefault",
            "--norestore",
            "--invisible",
            f"-env:UserInstallation=file://{profile_dir}",
            '--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager'
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=os.environ)
    
    def _wait_for_connection(self) -> None:
        """Wait for LibreOffice listener to become available."""
        max_wait = 5 if self.fast_mode else 15
        wait_interval = 0.2 if self.fast_mode else 0.5
        print("Starting LibreOffice listener...")
        
        for i in range(max_wait):
            time.sleep(wait_interval)
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                result = sock.connect_ex(('127.0.0.1', 2002))
                sock.close()
                if result == 0:
                    print(f"LibreOffice listener ready after {(i+1)*wait_interval:.1f} seconds")
                    return
            except:
                pass
            if not self.fast_mode or i % 5 == 0:  # Reduce log spam in fast mode
                print(f"Waiting for LibreOffice... ({i+1}/{max_wait})")
        
        print("WARNING: LibreOffice listener may not be ready")
    
    def connect(self) -> bool:
        """
        Connect to running LibreOffice instance.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            import uno
            local_ctx = uno.getComponentContext()
            resolver = local_ctx.ServiceManager.createInstanceWithContext(
                "com.sun.star.bridge.UnoUrlResolver", local_ctx)
            
            print("Connecting to LibreOffice...")
            max_attempts = 3 if self.fast_mode else 10
            retry_delay = 0.5 if self.fast_mode else 2
            
            for attempt in range(max_attempts):
                try:
                    self.ctx = resolver.resolve(
                        "uno:socket,host=127.0.0.1,port=2002;urp;StarOffice.ComponentContext")
                    print(f"✅ Connected to LibreOffice (attempt {attempt + 1})")
                    break
                except Exception as e:
                    if attempt < max_attempts - 1:
                        if not self.fast_mode or attempt == 0:  # Reduce log spam in fast mode
                            print(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        print(f"❌ Could not connect to LibreOffice listener after {max_attempts} attempts. Error: {e}", 
                              file=sys.stderr)
                        print("Make sure LibreOffice is running with --launch flag or start it externally.", 
                              file=sys.stderr)
                        return False
            
            if not self.ctx:
                print("Could not establish LibreOffice context.", file=sys.stderr)
                return False
            
            self.smgr = self.ctx.ServiceManager
            self.desktop = self.smgr.createInstanceWithContext("com.sun.star.frame.Desktop", self.ctx)
            return True
            
        except ImportError:
            print("ERROR: UNO bridge not available. Run with LibreOffice's Python (recommended).", 
                  file=sys.stderr)
            return False
    
    def load_document(self, file_path: str, hidden: bool = True) -> Any:
        """
        Load a document in LibreOffice.
        
        Args:
            file_path: Path to the document file
            hidden: Whether to load document hidden
            
        Returns:
            LibreOffice document object
        """
        if not self.desktop:
            raise RuntimeError("LibreOffice not connected. Call connect() first.")
        
        file_url = to_url(file_path)
        props = (mkprop("Hidden", hidden),) if hidden else ()
        
        print(f"🔍 Loading document from: {file_path}")
        print(f"🔍 File exists: {os.path.exists(file_path)}")
        if os.path.exists(file_path):
            print(f"🔍 File size: {os.path.getsize(file_path)} bytes")
        
        doc = self.desktop.loadComponentFromURL(file_url, "_blank", 0, props)
        print(f"✅ LibreOffice loaded document successfully")
        return doc
    
    def save_document(self, doc: Any, output_path: str) -> None:
        """
        Save document as DOCX format.
        
        Args:
            doc: LibreOffice document object
            output_path: Path where to save the document
        """
        out_props = (mkprop("FilterName", "MS Word 2007 XML"),)
        doc.storeToURL(to_url(output_path), out_props)
        doc.close(True)
        print("Done. Wrote:", output_path)
    
    def setup_document_author(self, doc: Any, author_name: str = "Secfix AI") -> None:
        """
        Setup document author and tracking properties.
        
        Args:
            doc: LibreOffice document object
            author_name: Author name to set
        """
        if self.fast_mode:
            print("⚡ Fast mode: Skipping document metadata setup")
            return
        
        try:
            # Set document properties
            doc_info = doc.getDocumentInfo()
            doc_info.setPropertyValue("Author", author_name)
            doc_info.setPropertyValue("ModifiedBy", author_name)
            
            # Set redline author
            try:
                doc.setPropertyValue("RedlineAuthor", author_name)
            except Exception:
                pass
            
            # Try to set user profile
            self._set_user_profile(author_name)
            
        except Exception as e:
            print(f"Warning: Could not set document author: {e}")
    
    def _set_user_profile(self, author_name: str) -> None:
        """Set user profile for tracked changes."""
        try:
            config_provider = self.smgr.createInstance("com.sun.star.configuration.ConfigurationProvider")
            config_access = config_provider.createInstanceWithArguments(
                "com.sun.star.configuration.ConfigurationUpdateAccess",
                (mkprop("nodepath", "/org.openoffice.UserProfile/Data"),)
            )
            if config_access:
                # Split author name
                name_parts = author_name.split(' ', 1)
                given_name = name_parts[0] if name_parts else author_name
                surname = name_parts[1] if len(name_parts) > 1 else ""
                
                config_access.setPropertyValue("givenname", given_name)
                config_access.setPropertyValue("sn", surname)
                config_access.commitChanges()
                print("✅ Set user profile for tracked changes")
        except Exception as e:
            print(f"Could not set user profile: {e}")
    
    def enable_tracking(self, doc: Any, enabled: bool = True) -> None:
        """
        Enable or disable tracked changes.
        
        Args:
            doc: LibreOffice document object
            enabled: Whether to enable tracking
        """
        try:
            doc.RecordChanges = enabled
            status = "enabled" if enabled else "disabled"
            print(f"✅ Tracking {status}")
        except Exception as e:
            print(f"Warning: Could not set tracking to {enabled}: {e}")


def mkprop(name: str, value: Any) -> Any:
    """
    Create a PropertyValue object for LibreOffice.
    
    Args:
        name: Property name
        value: Property value
        
    Returns:
        PropertyValue object
    """
    try:
        from com.sun.star.beans import PropertyValue
        p = PropertyValue()
        p.Name = name
        p.Value = value
        return p
    except ImportError:
        raise RuntimeError("UNO bridge not available")


def to_url(path: str) -> str:
    """
    Convert file path to URL format for LibreOffice.
    
    Args:
        path: File system path
        
    Returns:
        URL string
    """
    return Path(path).absolute().as_uri()


def get_redline_type(redline: Any) -> str:
    """
    Detect a redline's type ("insert" or "delete").
    
    Args:
        redline: LibreOffice redline object
        
    Returns:
        Lowercase string ("insert", "delete") or empty string if unknown
    """
    # Common property names observed across LO builds
    candidate_keys = ("RedlineType", "Type", "RedLineType", "RedlineKind")
    for key in candidate_keys:
        try:
            value = redline.getPropertyValue(key)
            if isinstance(value, str) and value:
                return value.strip().lower()
        except Exception:
            pass
    
    # Boolean flags in some builds
    try:
        if redline.getPropertyValue("IsDeletion"):
            return "delete"
    except Exception:
        pass
    try:
        if redline.getPropertyValue("IsInsertion"):
            return "insert"
    except Exception:
        pass
    
    return ""


def create_libreoffice_datetime() -> Any:
    """
    Create a LibreOffice DateTime object for annotations.
    
    Returns:
        DateTime object or Unix timestamp as fallback
    """
    try:
        from com.sun.star.util import DateTime
        import datetime
        now = datetime.datetime.now()
        dt = DateTime()
        dt.Year = now.year
        dt.Month = now.month
        dt.Day = now.day
        dt.Hours = now.hour
        dt.Minutes = now.minute
        dt.Seconds = now.second
        dt.NanoSeconds = now.microsecond * 1000
        return dt
    except Exception:
        # Fallback to Unix timestamp
        import time
        return time.time()

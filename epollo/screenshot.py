"""HTML rendering and screenshot functionality using Playwright."""

import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import base64

logger = logging.getLogger(__name__)


class ScreenshotRenderer:
    """HTML to screenshot renderer using Playwright."""
    
    def __init__(self, headless: bool = True, viewport: Optional[Dict[str, int]] = None):
        """Initialize screenshot renderer.
        
        Args:
            headless: Whether to run browser in headless mode
            viewport: Viewport dimensions {'width': 1200, 'height': 800}
        """
        self.headless = headless
        self.viewport = viewport or {'width': 1200, 'height': 800}
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()
    
    async def start(self):
        """Start the browser instance."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                viewport={'width': self.viewport['width'], 'height': self.viewport['height']},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            logger.info("Screenshot renderer started successfully")
        except Exception as e:
            logger.error(f"Failed to start screenshot renderer: {e}")
            raise
    
    async def stop(self):
        """Stop the browser instance."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("Screenshot renderer stopped")
        except Exception as e:
            logger.error(f"Error stopping screenshot renderer: {e}")
    
    async def render_html_to_screenshot(
        self,
        html: str,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        full_page: bool = True,
        quality: int = 90,
        format: str = 'png'
    ) -> bytes:
        """Render HTML content to screenshot.
        
        Args:
            html: HTML content to render
            output_path: Optional path to save screenshot
            width: Optional width override
            height: Optional height override  
            full_page: Whether to capture full page
            quality: Image quality (1-100) for JPEG
            format: Image format ('png', 'jpeg', 'webp')
            
        Returns:
            Screenshot as bytes
        """
        if not self.context:
            raise RuntimeError("Renderer not started. Call start() or use async context manager.")
        
        page: Page = await self.context.new_page()
        
        try:
            # Set viewport if custom dimensions provided
            if width or height:
                viewport_width = width or self.viewport['width']
                viewport_height = height or self.viewport['height']
                await page.set_viewport_size({'width': viewport_width, 'height': viewport_height})
            
            # Load HTML content
            await page.set_content(html, wait_until='networkidle')
            
            # Wait a bit for any dynamic content to load
            await page.wait_for_timeout(1000)
            
            # Take screenshot
            screenshot_options = {
                'full_page': full_page,
                'type': format
            }
            
            if format.lower() in ['jpeg', 'jpg']:
                screenshot_options['quality'] = quality
            
            screenshot_bytes = await page.screenshot(**screenshot_options)
            
            # Save to file if path provided
            if output_path:
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path_obj, 'wb') as f:
                    f.write(screenshot_bytes)
                logger.info(f"Screenshot saved to {output_path}")
            
            return screenshot_bytes
            
        except Exception as e:
            logger.error(f"Error rendering HTML to screenshot: {e}")
            raise
        finally:
            await page.close()
    
    async def render_url_to_screenshot(
        self,
        url: str,
        output_path: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        full_page: bool = True,
        quality: int = 90,
        format: str = 'png',
        wait_until: str = 'networkidle',
        timeout: int = 30000
    ) -> bytes:
        """Render URL to screenshot.
        
        Args:
            url: URL to render
            output_path: Optional path to save screenshot
            width: Optional width override
            height: Optional height override
            full_page: Whether to capture full page
            quality: Image quality (1-100) for JPEG
            format: Image format ('png', 'jpeg', 'webp')
            wait_until: When to consider navigation complete ('load', 'domcontentloaded', 'networkidle')
            timeout: Navigation timeout in milliseconds
            
        Returns:
            Screenshot as bytes
        """
        if not self.context:
            raise RuntimeError("Renderer not started. Call start() or use async context manager.")
        
        page: Page = await self.context.new_page()
        
        try:
            # Set viewport if custom dimensions provided
            if width or height:
                viewport_width = width or self.viewport['width']
                viewport_height = height or self.viewport['height']
                await page.set_viewport_size({'width': viewport_width, 'height': viewport_height})
            
            # Navigate to URL
            await page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # Wait a bit for any dynamic content to load
            await page.wait_for_timeout(1000)
            
            # Take screenshot
            screenshot_options = {
                'full_page': full_page,
                'type': format
            }
            
            if format.lower() in ['jpeg', 'jpg']:
                screenshot_options['quality'] = quality
            
            screenshot_bytes = await page.screenshot(**screenshot_options)
            
            # Save to file if path provided
            if output_path:
                output_path_obj = Path(output_path)
                output_path_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path_obj, 'wb') as f:
                    f.write(screenshot_bytes)
                logger.info(f"Screenshot saved to {output_path}")
            
            return screenshot_bytes
            
        except Exception as e:
            logger.error(f"Error rendering URL to screenshot: {e}")
            raise
        finally:
            await page.close()


def render_html_to_screenshot_sync(
    html: str,
    output_path: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    full_page: bool = True,
    quality: int = 90,
    format: str = 'png',
    headless: bool = True
) -> bytes:
    """Synchronous wrapper for HTML to screenshot rendering.
    
    Args:
        html: HTML content to render
        output_path: Optional path to save screenshot
        width: Image width
        height: Image height
        full_page: Whether to capture full page
        quality: Image quality (1-100) for JPEG
        format: Image format ('png', 'jpeg', 'webp')
        headless: Whether to run browser in headless mode
        
    Returns:
        Screenshot as bytes
    """
    async def _render():
        viewport = {'width': width, 'height': height}
        async with ScreenshotRenderer(headless=headless, viewport=viewport) as renderer:
            return await renderer.render_html_to_screenshot(
                html=html,
                output_path=output_path,
                width=width,
                height=height,
                full_page=full_page,
                quality=quality,
                format=format
            )
    
    return asyncio.run(_render())


def render_url_to_screenshot_sync(
    url: str,
    output_path: Optional[str] = None,
    width: int = 1200,
    height: int = 800,
    full_page: bool = True,
    quality: int = 90,
    format: str = 'png',
    headless: bool = True,
    wait_until: str = 'networkidle',
    timeout: int = 30000
) -> bytes:
    """Synchronous wrapper for URL to screenshot rendering.
    
    Args:
        url: URL to render
        output_path: Optional path to save screenshot
        width: Image width
        height: Image height
        full_page: Whether to capture full page
        quality: Image quality (1-100) for JPEG
        format: Image format ('png', 'jpeg', 'webp')
        headless: Whether to run browser in headless mode
        wait_until: When to consider navigation complete
        timeout: Navigation timeout in milliseconds
        
    Returns:
        Screenshot as bytes
    """
    async def _render():
        viewport = {'width': width, 'height': height}
        async with ScreenshotRenderer(headless=headless, viewport=viewport) as renderer:
            return await renderer.render_url_to_screenshot(
                url=url,
                output_path=output_path,
                width=width,
                height=height,
                full_page=full_page,
                quality=quality,
                format=format,
                wait_until=wait_until,
                timeout=timeout
            )
    
    return asyncio.run(_render())
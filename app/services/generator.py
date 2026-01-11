"""Star map image generation using Skyfield astronomy library."""
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server - MUST be before pyplot import
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from skyfield.api import Star, load, wgs84, Loader
from skyfield.data import hipparcos

# Data directory for ephemeris files
DATA_DIR = Path(__file__).parent.parent.parent / "data"


class StarMapGenerator:
    """Generates star map images using Skyfield astronomy library."""
    
    # Default visual settings
    LIMITING_MAGNITUDE = 6.0
    FIGURE_SIZE = (10, 12)
    DPI = 150
    BACKGROUND_COLOR = "#0a1628"
    BORDER_COLOR = "#7cb342"
    STAR_COLOR = "#e8f5e9"
    CONSTELLATION_LINE_COLOR = "#4a5568"
    TEXT_COLOR = "#a5d6a7"
    
    def __init__(self):
        self._stars = None
        self._eph = None
    
    def _load_stars(self):
        """Load Hipparcos star catalog (cached)."""
        if self._stars is None:
            with load.open(hipparcos.URL) as f:
                self._stars = hipparcos.load_dataframe(f)
        return self._stars
    
    def _load_ephemeris(self):
        """Load JPL ephemeris (cached)."""
        if self._eph is None:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            loader = Loader(str(DATA_DIR))
            self._eph = loader('de421.bsp')
        return self._eph
    
    def generate(
        self,
        latitude: float,
        longitude: float,
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        timezone_offset: int,
        title: str = "THE NIGHT SKY"
    ) -> bytes:
        """
        Generate a star map PNG image.
        
        Returns:
            PNG image as bytes
        """
        stars = self._load_stars()
        eph = self._load_ephemeris()
        
        # Create observation time
        ts = load.timescale()
        tz = timezone(timedelta(hours=timezone_offset))
        dt = datetime(year, month, day, hour, minute, tzinfo=tz)
        t = ts.from_datetime(dt)
        
        # Observer location
        observer = wgs84.latlon(latitude, longitude)
        earth = eph['earth']
        location = earth + observer
        
        # Compute star positions
        star_positions = Star.from_dataframe(stars)
        astrometric = location.at(t).observe(star_positions)
        apparent = astrometric.apparent()
        alt, az, _ = apparent.altaz()
        
        alt_deg = alt.degrees
        az_deg = az.degrees
        
        # Filter visible stars
        visible = (alt_deg > 0) & (stars['magnitude'] <= self.LIMITING_MAGNITUDE)
        visible_stars = stars[visible].copy()
        visible_alt = alt_deg[visible]
        visible_az = az_deg[visible]
        
        # Stereographic projection
        alt_rad = np.radians(visible_alt)
        az_rad = np.radians(visible_az)
        r = np.cos(alt_rad) / (1 + np.sin(alt_rad))
        x = r * np.sin(az_rad)
        y = -r * np.cos(az_rad)
        
        # Star sizes based on magnitude
        magnitudes = visible_stars['magnitude'].values
        sizes = (self.LIMITING_MAGNITUDE - magnitudes + 1) ** 2 * 2
        
        # Create figure
        fig, ax = plt.subplots(figsize=self.FIGURE_SIZE, facecolor=self.BACKGROUND_COLOR)
        ax.set_facecolor(self.BACKGROUND_COLOR)
        
        # Draw border
        border = Circle((0, 0), 1.0, fill=False, edgecolor=self.BORDER_COLOR, linewidth=2)
        ax.add_patch(border)
        
        # Draw horizon
        horizon = Circle((0, 0), 0.98, fill=True, facecolor=self.BACKGROUND_COLOR,
                        edgecolor=self.BORDER_COLOR, linewidth=1)
        ax.add_patch(horizon)
        
        # Altitude reference circles
        for alt_line in [30, 60]:
            r_line = np.cos(np.radians(alt_line)) / (1 + np.sin(np.radians(alt_line)))
            circle = Circle((0, 0), r_line, fill=False, edgecolor=self.CONSTELLATION_LINE_COLOR,
                           linewidth=0.5, linestyle='--', alpha=0.3)
            ax.add_patch(circle)
        
        # Cardinal direction lines
        for angle in [0, 90, 180, 270]:
            rad = np.radians(angle)
            ax.plot([0, np.sin(rad)], [0, -np.cos(rad)],
                   color=self.CONSTELLATION_LINE_COLOR, linewidth=0.5, linestyle='--', alpha=0.3)
        
        # Plot stars
        ax.scatter(x, y, s=sizes, c=self.STAR_COLOR, alpha=0.9, edgecolors='none')
        
        # Cardinal direction labels
        for label, dx, dy in [('N', 0, -1.08), ('S', 0, 1.08), ('E', -1.08, 0), ('W', 1.08, 0)]:
            ax.text(dx, dy, label, ha='center', va='center',
                   color=self.TEXT_COLOR, fontsize=12, fontweight='bold')
        
        # Axis setup
        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-1.25, 1.25)
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Title
        ax.text(0, 1.18, title.upper(), ha='center', va='bottom',
               color=self.TEXT_COLOR, fontsize=16, fontweight='bold', fontfamily='serif')
        
        # Date subtitle
        month_names = ['', 'JANUARY', 'FEBRUARY', 'MARCH', 'APRIL', 'MAY', 'JUNE',
                      'JULY', 'AUGUST', 'SEPTEMBER', 'OCTOBER', 'NOVEMBER', 'DECEMBER']
        day_suffix = 'th'
        if day in [1, 21, 31]:
            day_suffix = 'st'
        elif day in [2, 22]:
            day_suffix = 'nd'
        elif day in [3, 23]:
            day_suffix = 'rd'
        
        date_str = f"{day}{day_suffix} {month_names[month]} {year}"
        ax.text(0, -1.12, date_str, ha='center', va='top',
               color=self.TEXT_COLOR, fontsize=10, fontfamily='serif')
        
        # Coordinates
        lat_dir = 'N' if latitude >= 0 else 'S'
        lon_dir = 'W' if longitude < 0 else 'E'
        coord_str = f"{abs(latitude):.4f}° {lat_dir} {abs(longitude):.4f}° {lon_dir}"
        ax.text(0, -1.18, coord_str, ha='center', va='top',
               color=self.TEXT_COLOR, fontsize=9, fontfamily='serif', alpha=0.8)
        
        plt.tight_layout()
        
        # Save to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=self.DPI, facecolor=self.BACKGROUND_COLOR,
                   bbox_inches='tight', pad_inches=0.5)
        plt.close(fig)
        buf.seek(0)
        
        return buf.read()


# Singleton instance
generator = StarMapGenerator()


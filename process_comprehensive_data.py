#!/usr/bin/env python3
"""
Process Comprehensive Data from Play-by-Play
Converts play-by-play JSON files to comprehensive format for dashboard consumption
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataProcessor:
    """Process play-by-play data into comprehensive format"""
    
    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / 'data'
        
        self.data_dir = data_dir
        self.play_by_play_dir = data_dir / 'preseason' / 'play_by_play'
        self.comprehensive_dir = data_dir / 'preseason' / 'comprehensive'
        
        # Ensure comprehensive directory exists
        self.comprehensive_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_count = 0
        self.failed_count = 0
    
    def extract_player_from_play_text(self, play_text: str, play_type: str) -> Optional[str]:
        """Extract player names from play text based on play type"""
        if not play_text:
            return None
        
        # Touchdown patterns
        if play_type == 'touchdown':
            patterns = [
                # Receiving touchdown: "Pass to [Player] for touchdown"
                r"pass.*?to\s+([A-Z]\.\s*[A-Za-z'\-]+).*?touchdown",
                # Rushing touchdown: "[Player] [yards] yard run for touchdown"
                r"([A-Z]\.\s*[A-Za-z'\-]+)\s+\d+\s+yard.*?run.*?touchdown",
                # General touchdown pattern
                r"([A-Z]\.\s*[A-Za-z'\-]+).*?touchdown",
            ]
        elif play_type == 'interception':
            patterns = [
                r"intercepted.*?by\s+([A-Z]\.\s*[A-Za-z'\-]+)",
                r"([A-Z]\.\s*[A-Za-z'\-]+).*?intercept",
            ]
        elif play_type == 'fumble':
            patterns = [
                r"([A-Z]\.\s*[A-Za-z'\-]+).*?fumble",
                r"fumble.*?by\s+([A-Z]\.\s*[A-Za-z'\-]+)",
            ]
        else:
            return None
        
        for pattern in patterns:
            match = re.search(pattern, play_text, re.IGNORECASE)
            if match:
                player_name = match.group(1).strip()
                # Clean up the player name
                player_name = re.sub(r'\s+', ' ', player_name)
                return player_name
        
        return None
    
    def process_play_by_play_file(self, file_path: Path) -> Optional[Dict]:
        """Process a single play-by-play file into comprehensive format"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Extract basic game info
            game_info = data.get('game_info', {})
            drives = data.get('drives', [])
            plays = data.get('plays', [])
            
            if not game_info.get('game_id'):
                logger.warning(f"No game ID found in {file_path}")
                return None
            
            # Create comprehensive structure with box score and play-by-play
            comprehensive = {
                'game_id': game_info['game_id'],
                'date': file_path.stem.split('_')[0],  # Extract date from filename
                'box_score': {
                    'game_info': {
                        'game_id': game_info['game_id'],
                        'date': game_info.get('date', ''),
                        'status': game_info.get('status', {}),
                        'venue': game_info.get('venue', {}),
                        'attendance': 0
                    },
                    'team_stats': self._create_team_stats(game_info),
                    'player_stats': {},
                    'scoring_summary': []
                },
                'play_by_play': {
                    'game_info': game_info,
                    'drives': drives,
                    'plays': plays,
                    'scoring_plays': self._extract_scoring_plays(plays),
                    'touchdowns': self._extract_touchdowns(plays),
                    'interceptions': self._extract_interceptions(plays),
                    'fumbles': self._extract_fumbles(plays)
                },
                'processing_timestamp': datetime.now().isoformat()
            }
            
            return comprehensive
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return None
    
    def _create_team_stats(self, game_info: Dict) -> Dict:
        """Create team stats from game info"""
        team_stats = {}
        
        teams = game_info.get('teams', [])
        for team in teams:
            abbr = team.get('abbreviation', 'UNK')
            team_stats[abbr] = {
                'score': int(team.get('score', 0)),
                'record': '0-0',  # Preseason record
                'home_away': team.get('home_away', 'unknown')
            }
        
        return team_stats
    
    def _extract_scoring_plays(self, plays: List[Dict]) -> List[Dict]:
        """Extract all scoring plays"""
        scoring_plays = []
        
        for play in plays:
            if play.get('scoring_play', False):
                scoring_plays.append(play)
        
        return scoring_plays
    
    def _extract_touchdowns(self, plays: List[Dict]) -> List[Dict]:
        """Extract touchdown plays with player names"""
        touchdowns = []
        
        for play in plays:
            play_text = play.get('text', '').lower()
            if 'touchdown' in play_text:
                player = self.extract_player_from_play_text(play.get('text', ''), 'touchdown')
                td_play = play.copy()
                if player:
                    td_play['player'] = player
                touchdowns.append(td_play)
        
        return touchdowns
    
    def _extract_interceptions(self, plays: List[Dict]) -> List[Dict]:
        """Extract interception plays with player names"""
        interceptions = []
        
        for play in plays:
            play_text = play.get('text', '').lower()
            if 'intercept' in play_text:
                player = self.extract_player_from_play_text(play.get('text', ''), 'interception')
                int_play = play.copy()
                if player:
                    int_play['player'] = player
                interceptions.append(int_play)
        
        return interceptions
    
    def _extract_fumbles(self, plays: List[Dict]) -> List[Dict]:
        """Extract fumble plays with player names"""
        fumbles = []
        
        for play in plays:
            play_text = play.get('text', '').lower()
            if 'fumble' in play_text:
                player = self.extract_player_from_play_text(play.get('text', ''), 'fumble')
                fumble_play = play.copy()
                if player:
                    fumble_play['player'] = player
                fumbles.append(fumble_play)
        
        return fumbles
    
    def process_recent_files(self, date_pattern: str = None) -> Dict:
        """Process recent play-by-play files"""
        logger.info("Processing play-by-play files to comprehensive format")
        
        # Find files to process
        if date_pattern:
            pattern = f"{date_pattern}*_play_by_play.json"
        else:
            pattern = "*_play_by_play.json"
        
        files_to_process = list(self.play_by_play_dir.glob(pattern))
        files_to_process.sort()  # Process in chronological order
        
        logger.info(f"Found {len(files_to_process)} play-by-play files to process")
        
        for file_path in files_to_process:
            try:
                # Check if comprehensive file already exists and is recent
                comprehensive_file = self.comprehensive_dir / f"{file_path.stem.replace('_play_by_play', '_complete')}.json"
                
                if comprehensive_file.exists():
                    # Check if source is newer than comprehensive
                    source_mtime = file_path.stat().st_mtime
                    comp_mtime = comprehensive_file.stat().st_mtime
                    
                    if comp_mtime > source_mtime:
                        logger.info(f"Skipping {file_path.name} - comprehensive file is newer")
                        continue
                
                logger.info(f"Processing {file_path.name}")
                
                comprehensive = self.process_play_by_play_file(file_path)
                if comprehensive:
                    # Write comprehensive file
                    with open(comprehensive_file, 'w') as f:
                        json.dump(comprehensive, f, indent=2)
                    
                    self.processed_count += 1
                    logger.info(f"Created {comprehensive_file.name}")
                else:
                    self.failed_count += 1
                    logger.error(f"Failed to process {file_path.name}")
                    
            except Exception as e:
                self.failed_count += 1
                logger.error(f"Error processing {file_path.name}: {e}")
        
        return {
            'processed': self.processed_count,
            'failed': self.failed_count,
            'total': len(files_to_process)
        }

def main():
    """Command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process NFL play-by-play to comprehensive format')
    parser.add_argument('--date-pattern', help='Process files matching date pattern (e.g., 2025-08-22)')
    parser.add_argument('--all', action='store_true', help='Process all play-by-play files')
    
    args = parser.parse_args()
    
    processor = ComprehensiveDataProcessor()
    
    date_pattern = args.date_pattern if args.date_pattern else None
    if args.all:
        date_pattern = None
    
    result = processor.process_recent_files(date_pattern)
    
    print(f"\nComprehensive Data Processing Summary:")
    print(f"  Total files: {result['total']}")
    print(f"  Processed: {result['processed']}")
    print(f"  Failed: {result['failed']}")
    
    if result['failed'] > 0:
        print(f"\n⚠️  {result['failed']} files failed to process")
        sys.exit(1)
    else:
        print(f"\n✅ All files processed successfully")

if __name__ == "__main__":
    main()
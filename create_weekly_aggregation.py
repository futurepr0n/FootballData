#!/usr/bin/env python3
"""
Create Weekly Aggregation from Existing Comprehensive Data
Converts existing comprehensive game files into the weekly format expected by the enhanced FootballAPI
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WeeklyAggregator:
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = Path(__file__).parent / 'data'
        
        self.data_dir = Path(data_dir)
        self.comprehensive_dir = self.data_dir / 'preseason' / 'comprehensive'
        self.output_dir = self.data_dir
        
        # Week date ranges for preseason 2025
        self.week_ranges = {
            1: ('2025-08-01', '2025-08-11'),  # Week 1: Aug 1-11
            2: ('2025-08-12', '2025-08-18'),  # Week 2: Aug 12-18  
            3: ('2025-08-19', '2025-08-25'),  # Week 3: Aug 19-25
            4: ('2025-08-26', '2025-08-31'),  # Week 4: Aug 26-31
        }
        
    def extract_player_stats_from_comprehensive(self, comprehensive_data):
        """Extract player statistics from comprehensive game data"""
        player_stats = {
            'passing': [],
            'rushing': [],
            'receiving': [],
            'defensive': []
        }
        
        # Extract from play-by-play touchdowns
        touchdowns = comprehensive_data.get('play_by_play', {}).get('touchdowns', [])
        interceptions = comprehensive_data.get('play_by_play', {}).get('interceptions', [])
        
        # Process touchdowns to extract passing/rushing/receiving stats
        processed_players = set()
        
        for td in touchdowns:
            player_name = td.get('player')
            if not player_name or player_name in processed_players:
                continue
                
            text = td.get('text', '')
            text_lower = text.lower()
            team = self._extract_team_from_play(td, comprehensive_data)
            
            if 'pass' in text_lower and 'to' in text_lower:
                # Passing touchdown - extract both passer and receiver
                passer = self._extract_passer_from_text(text)  # Use original text for regex
                receiver = player_name  # The 'player' field from touchdown data
                
                # Add passer statistics
                if passer:
                    player_stats['passing'].append({
                        'player_id': f"player_{passer.replace(' ', '_')}",
                        'name': passer,
                        'team': team,
                        'team_abbrev': team[:3].upper(),
                        'completions': 1,
                        'attempts': 1,
                        'yards': self._extract_yards_from_text(text_lower),
                        'touchdowns': 1,
                        'interceptions': 0
                    })
                
                # Add receiver statistics  
                if receiver:
                    player_stats['receiving'].append({
                        'player_id': f"player_{receiver.replace(' ', '_')}",
                        'name': receiver,
                        'team': team,
                        'team_abbrev': team[:3].upper(),
                        'receptions': 1,
                        'yards': self._extract_yards_from_text(text_lower),
                        'touchdowns': 1
                    })
            elif 'run' in text_lower or 'rush' in text_lower:
                # Rushing touchdown
                player_stats['rushing'].append({
                    'player_id': f"player_{player_name.replace(' ', '_')}",
                    'name': player_name,
                    'team': team,
                    'team_abbrev': team[:3].upper(),
                    'carries': 1,
                    'yards': self._extract_yards_from_text(text),
                    'touchdowns': 1
                })
            
            processed_players.add(player_name)
        
        # Process interceptions
        for interception in interceptions:
            player_name = interception.get('player')
            if not player_name:
                continue
                
            team = self._extract_team_from_play(interception, comprehensive_data)
            player_stats['defensive'].append({
                'player_id': f"player_{player_name.replace(' ', '_')}",
                'name': player_name,
                'team': team,
                'team_abbrev': team[:3].upper(),
                'interceptions': 1,
                'tackles': 0,
                'sacks': 0
            })
        
        return player_stats
    
    def _extract_team_from_play(self, play, comprehensive_data):
        """Extract team from play context"""
        # Try to get team from team stats
        team_stats = comprehensive_data.get('box_score', {}).get('team_stats', {})
        if len(team_stats) >= 2:
            teams = list(team_stats.keys())
            return comprehensive_data.get('box_score', {}).get('game_info', {}).get('teams', [{}])[0].get('name', teams[0])
        return 'Unknown Team'
    
    def _extract_yards_from_text(self, text):
        """Extract yardage from play text"""
        match = re.search(r'(\d+)\s*yard', text.lower())
        return int(match.group(1)) if match else 0
    
    def _extract_passer_from_text(self, text):
        """Extract passer name from touchdown text"""
        # Look for pattern: (Formation) Passer pass to Receiver
        match = re.search(r'^\([^)]*\)\s*([A-Z]\.[A-Za-z]+)\s+pass', text)
        if match:
            return match.group(1)
        return None
    
    def get_week_for_date(self, date_str):
        """Determine which preseason week a date belongs to"""
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        
        for week, (start_date, end_date) in self.week_ranges.items():
            start_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_obj = datetime.strptime(end_date, '%Y-%m-%d')
            
            if start_obj <= date_obj <= end_obj:
                return week
        
        return None
    
    def extract_game_info(self, comprehensive_data, filename):
        """Extract basic game information"""
        box_score = comprehensive_data.get('box_score', {})
        game_info = box_score.get('game_info', {})
        team_stats = box_score.get('team_stats', {})
        
        # Extract teams and scores with proper mapping
        teams = []
        for team_abbrev, stats in team_stats.items():
            teams.append({
                'name': f"{team_abbrev}",  # Use abbreviation as name for now
                'abbreviation': team_abbrev,
                'score': int(stats.get('score', 0)),
                'home_away': stats.get('home_away', 'unknown')
            })
        
        # Get actual game status from comprehensive data
        status_obj = game_info.get('status', {})
        if isinstance(status_obj, dict):
            # Check if it's a nested status structure
            type_obj = status_obj.get('type', {})
            if isinstance(type_obj, dict):
                game_status = type_obj.get('description', 'Final')
                is_completed = type_obj.get('completed', False)
            else:
                game_status = status_obj.get('description', 'Final')
                is_completed = True  # Assume completed if in comprehensive data
        else:
            game_status = str(status_obj)
            is_completed = True
        
        # Determine final display name based on scores
        if len(teams) >= 2:
            away_team = next((t for t in teams if t.get('home_away') == 'away'), teams[0])
            home_team = next((t for t in teams if t.get('home_away') == 'home'), teams[1])
            
            if is_completed and (away_team.get('score', 0) > 0 or home_team.get('score', 0) > 0):
                # Show final score in name
                name = f"{away_team['abbreviation']} {away_team['score']}, {home_team['abbreviation']} {home_team['score']}"
            else:
                name = f"{away_team['abbreviation']} @ {home_team['abbreviation']}"
        else:
            name = "Unknown Game"
        
        return {
            'id': comprehensive_data.get('game_id', filename.split('_')[1]),  # Get game ID correctly
            'date': comprehensive_data.get('date', filename.split('_')[0]),
            'name': name,
            'status': game_status,
            'completed': is_completed,
            'home_team': next((t for t in teams if t.get('home_away') == 'home'), teams[0] if teams else {}),
            'away_team': next((t for t in teams if t.get('home_away') == 'away'), teams[1] if len(teams) > 1 else {}),
        }
    
    def aggregate_by_weeks(self):
        """Aggregate comprehensive data into weekly structure"""
        logger.info(f"Scanning comprehensive directory: {self.comprehensive_dir}")
        
        if not self.comprehensive_dir.exists():
            logger.error(f"Comprehensive directory not found: {self.comprehensive_dir}")
            return False
        
        # Group files by week
        weekly_data = defaultdict(lambda: {
            'week': 0,
            'season': 2025,
            'games': [],
            'player_stats': {
                'passing': [],
                'rushing': [], 
                'receiving': [],
                'defensive': []
            }
        })
        
        files = list(self.comprehensive_dir.glob('*_complete.json'))
        logger.info(f"Found {len(files)} comprehensive files")
        
        for file_path in sorted(files):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                # Extract date from filename: YYYY-MM-DD_GAMEID_complete.json
                filename = file_path.name
                date_str = filename.split('_')[0]  # Get YYYY-MM-DD part
                
                week = self.get_week_for_date(date_str)
                if not week:
                    logger.warning(f"Could not determine week for {filename}, skipping")
                    continue
                
                # Initialize week data
                weekly_data[week]['week'] = week
                weekly_data[week]['season'] = 2025
                
                # Extract game info
                game_info = self.extract_game_info(data, filename)
                weekly_data[week]['games'].append(game_info)
                
                # Extract and aggregate player stats
                player_stats = self.extract_player_stats_from_comprehensive(data)
                
                for stat_type, stats in player_stats.items():
                    weekly_data[week]['player_stats'][stat_type].extend(stats)
                
                logger.info(f"Processed {filename} -> Week {week}")
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                continue
        
        # Save weekly files
        saved_count = 0
        for week, data in weekly_data.items():
            try:
                output_file = self.output_dir / f"week_{week:02d}_2025.json"
                
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                
                games_count = len(data['games'])
                stats_count = sum(len(stats) for stats in data['player_stats'].values())
                
                logger.info(f"Saved {output_file}: {games_count} games, {stats_count} player stats")
                saved_count += 1
                
            except Exception as e:
                logger.error(f"Error saving week {week}: {e}")
        
        logger.info(f"Successfully created {saved_count} weekly aggregation files")
        return saved_count > 0
    
    def create_summary(self):
        """Create a summary of the aggregated data"""
        summary = {
            'created_at': datetime.now().isoformat(),
            'weeks': {},
            'totals': {
                'total_weeks': 0,
                'total_games': 0,
                'total_player_performances': 0
            }
        }
        
        # Check each week file
        for week in range(1, 5):  # Preseason weeks 1-4
            week_file = self.output_dir / f"week_{week:02d}_2025.json"
            
            if week_file.exists():
                try:
                    with open(week_file, 'r') as f:
                        data = json.load(f)
                    
                    games_count = len(data.get('games', []))
                    stats_count = sum(len(stats) for stats in data.get('player_stats', {}).values())
                    
                    summary['weeks'][week] = {
                        'games': games_count,
                        'player_performances': stats_count,
                        'categories': {
                            category: len(stats) 
                            for category, stats in data.get('player_stats', {}).items()
                        }
                    }
                    
                    summary['totals']['total_weeks'] += 1
                    summary['totals']['total_games'] += games_count
                    summary['totals']['total_player_performances'] += stats_count
                    
                except Exception as e:
                    logger.error(f"Error reading week {week} summary: {e}")
        
        # Save summary
        summary_file = self.output_dir / 'aggregation_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Created aggregation summary: {summary_file}")
        return summary

def main():
    aggregator = WeeklyAggregator()
    
    logger.info("Starting weekly data aggregation...")
    
    if aggregator.aggregate_by_weeks():
        summary = aggregator.create_summary()
        
        print(f"\n✅ Weekly Aggregation Complete!")
        print(f"   Total weeks: {summary['totals']['total_weeks']}")
        print(f"   Total games: {summary['totals']['total_games']}")
        print(f"   Total player performances: {summary['totals']['total_player_performances']}")
        
        print(f"\n📊 Week-by-week breakdown:")
        for week, stats in summary['weeks'].items():
            print(f"   Week {week}: {stats['games']} games, {stats['player_performances']} player stats")
        
        print(f"\n✅ Data ready for FootballAPI consumption!")
        return True
    else:
        print(f"\n❌ Weekly aggregation failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
import numpy as np
import pandas as pd
import streamlit as st

class BusSeatingAlgorithm:
    def __init__(self, rows=10, cols=4):
        self.rows = rows
        self.cols = cols
        self.total_seats = rows * cols
        self.seat_map = np.zeros((rows, cols), dtype=int)  # 0 = vide, 1 = occupé
        
    def get_seat_label(self, row, col):
        """Retourne le label du siège (ex: 1A, 1B, 2A, etc.)"""
        col_letter = chr(65 + col)  # A, B, C, D
        return f"{row+1}{col_letter}"
    
    def get_seat_position(self, seat_number):
        """Convertit un numéro de siège en position (row, col)"""
        seat_number -= 1  # 0-based
        row = seat_number // self.cols
        col = seat_number % self.cols
        return row, col
    
    def is_window_seat(self, row, col):
        """Vérifie si c'est un siège fenêtre"""
        return col == 0 or col == self.cols - 1
    
    def is_aisle_seat(self, row, col):
        """Vérifie si c'est un siège couloir"""
        return col == 1 or col == self.cols - 2
    
    def assign_seats(self, clients_df):
        """
        Algorithme intelligent de placement:
        1. Groupes (familles/amis) ensemble
        2. Filles ensemble, garçons ensemble
        3. Personnes âgées près des sorties (devant)
        4. Fenêtres prioritaires pour ceux qui les préfèrent
        """
        assignments = []
        seat_number = 1
        
        # Trier par groupe et catégorie
        clients_df = clients_df.sort_values(['group_id', 'category', 'id'])
        
        # Traiter les groupes d'abord
        grouped = clients_df.groupby('group_id') if 'group_id' in clients_df.columns else [(None, clients_df)]
        
        for group_id, group in grouped:
            if group_id is not None and not pd.isna(group_id):
                # Placer le groupe ensemble
                for _, client in group.iterrows():
                    row, col = self.get_seat_position(seat_number)
                    self.seat_map[row, col] = 1
                    assignments.append({
                        'user_id': client['id'],
                        'seat_number': seat_number,
                        'seat_row': row + 1,
                        'seat_col': col + 1,
                        'seat_label': self.get_seat_label(row, col),
                        'is_window': self.is_window_seat(row, col)
                    })
                    seat_number += 1
            else:
                # Traiter les individus selon catégorie
                for _, client in group.iterrows():
                    row, col = self.get_seat_position(seat_number)
                    
                    # Si personne âgée, essayer de mettre devant
                    if client.get('category') == 'elder' and seat_number > 8:
                        # Chercher une place devant
                        for r in range(min(2, self.rows)):
                            for c in range(self.cols):
                                if self.seat_map[r, c] == 0:
                                    row, col = r, c
                                    break
                    
                    self.seat_map[row, col] = 1
                    assignments.append({
                        'user_id': client['id'],
                        'seat_number': seat_number,
                        'seat_row': row + 1,
                        'seat_col': col + 1,
                        'seat_label': self.get_seat_label(row, col),
                        'is_window': self.is_window_seat(row, col)
                    })
                    seat_number += 1
        
        return assignments
    
    def get_seat_visualization(self):
        """Retourne une représentation visuelle du bus"""
        fig_data = []
        for row in range(self.rows):
            for col in range(self.cols):
                fig_data.append({
                    'row': row + 1,
                    'col': chr(65 + col),
                    'status': 'Occupé' if self.seat_map[row, col] == 1 else 'Libre',
                    'seat': self.get_seat_label(row, col)
                })
        return pd.DataFrame(fig_data)
  

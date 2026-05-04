#!/bin/bash
echo "Nettoyage des buffers audio, Monsieur Mathieu..."

# On ne tue que les processus utilisateur
pkill -u mathieu python 2>/dev/null

# On supprime les sockets morts sans toucher au serveur maître
rm -f /run/user/1000/pulse/*.lock 2>/dev/null

echo "Réinitialisation logicielle terminée. Prêt pour un nouvel essai."

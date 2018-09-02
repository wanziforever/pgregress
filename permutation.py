#!/usr/bin/env python

sessions = [
    {"steps": ['s1_1', 's1_2', 's1_3']},
    {"steps": ['s2_1', 's2_2', 's2_3']}
]

nsessions = len(sessions)
piles = [0] * nsessions

nsteps = 0
for session in sessions:
    nsteps += len(session['steps'])

steps = [''] * nsteps
nsteps = 0
def permutation(sessions, nsteps, steps):
    found = False
    for i in range(nsessions):
        if piles[i] < len(sessions[i]['steps']):
            steps[nsteps] = sessions[i]['steps'][piles[i]]
            piles[i] += 1
            yield from permutation(sessions, nsteps+1, steps)
            piles[i] -= 1
            found = True
            
    if found is False:    
        yield(steps)

generator = permutation(sessions, nsteps, steps)
for steps in generator:
    print(steps)

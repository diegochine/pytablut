import config as cfg
import loggers as lg
from game import Game
from memory import Memory, load_memories
from neuralnet import ResidualNN
from player import Player

lg.logger_train.info('=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*')
lg.logger_train.info('=*=*=*=*=*=.      NEW LOG      =*=*=*=*=*')
lg.logger_train.info('=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*')


def self_play(p1: Player, p2: Player, memory: Memory):
    """ play one match of self play, saving the (partial) results in memory"""
    game = Game()
    p1.reset()
    p2.reset()

    while not game.current_state.is_terminal:
        print('CURRENT TURN:', endgame_map[game.current_player])
        print(game.current_state.board, '\n')
        if game.current_player == 1:
            turn = 'WHITE'
            act, pi = p1.act(game.current_state)
        else:
            turn = 'BLACK'
            act, pi = p2.act(game.current_state)
        lg.logger_train.info('{} TURN, ACTION: {}'.format(turn, act))
        memory.commit_stmemory(game.current_state, pi, None)
        game.execute(act)

    if game.current_state.value == 0:  # it's a draw
        lg.logger_train.info("IT'S A DRAW")
        memory.commit_ltmemory(0)
    else:  # the player of this turn has lost
        memory.commit_ltmemory(-game.current_state.turn)
        lg.logger_train.info('WINNER OF THIS EPISODE: {}'.format(endgame_map[-game.current_state.turn]))


if __name__ == "__main__":
    # SETUP GAME
    endgame_map = {0: 'DRAW', 1: 'WHITE', -1: 'BLACK'}

    # LOAD MEMORY STORAGE
    ltmemory = load_memories()
    memory = Memory(cfg.MEMORY_SIZE, ltmemory)

    # CREATE (AND EVENTUALLY LOAD) NETWORKS
    general_nn = ResidualNN()
    lg.logger_train.info('LOADED NETWORK')

    # CREATE PLAYERS
    white = Player(color='WHITE', name='dc', nnet=general_nn,
                   timeout=cfg.TIMEOUT, simulations=cfg.MCTS_SIMULATIONS)
    black = Player(color='BLACK', name='pd', nnet=general_nn,
                   timeout=cfg.TIMEOUT, simulations=cfg.MCTS_SIMULATIONS)

    # START!
    lg.logger_train.info('PLAYERS READY, STARTING MAIN LOOP')
    for version in range(cfg.TOTAL_ITERATIONS):
        lg.logger_train.info('ITERATION NUMBER {:0>3d}/{:0>3d}'.format(version, cfg.TOTAL_ITERATIONS))
        lg.logger_train.info('SELF PLAYING FOR {:d} EPISODES'.format(cfg.EPISODES))

        # make sure both players use the same network
        black.brain.set_weights(white.brain.get_weights())

        for episode in range(cfg.EPISODES):
            lg.logger_train.info('EPISODE {:0>3d}/{:0>3d}'.format(episode, cfg.EPISODES))
            self_play(white, black, memory)

        memory.save('v{:0>3d}'.format(version))
        lg.logger_train.info('RETRAINING NETWORK')
        if len(memory) >= cfg.MIN_MEMORIES:
            white.replay(memory.ltmemory)
            #white.brain.save('general', version)

        # TODO evaluate network

from lichess.schemas import (
    GameStartEvent,
    GameFinishEvent,
    ChallengeEvent,
    ChallengeCanceledEvent,
    ChallengeDeclinedEvent,
    GameFullEvent,
    GameStateEvent,
    ChatLineEvent,
    OpponentGoneEvent,
)


IncomingEvent = (
    GameStartEvent | GameFinishEvent | ChallengeEvent | ChallengeCanceledEvent | ChallengeDeclinedEvent
)


BotGameEvent = GameFullEvent | GameStateEvent | ChatLineEvent | OpponentGoneEvent

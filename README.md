# MidjourneyWrapper

A REST API to access midjourney discord

## Configuration

update config.json before use this wrapper

- `user_token`: user account's token, please refer: [How to get your Discord token](https://www.androidauthority.com/get-discord-token-3149920/)
- `server_id/channel_id`: please refer: [Where can I find my User/Server/Message ID](https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID-)
- `proxy`: if you can access discord freely, no need this field

## Example Usage

```bash
# for single request
python3 example.py midjourneybot [--prompt {prompt}]
# for batch requests
python3 example.py batchbot [--prompt {prompt} --prompt {prompt}]
```

## TODO

- [ ] add async interface

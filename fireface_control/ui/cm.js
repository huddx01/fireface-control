var clients = {}

app.on('open', (data, client)=>{
    clients[client.id] = true
})

app.on('close', (data, client)=>{
    delete clients[client.id]
})

module.exports = {

    oscOutFilter: (data)=>{
        var {address, args, host, port, clientId} = data

        // manual client sync (default sync disabled to prevent state sync on connection)
        for (var id in clients) {
            if (id !== clientId) receive(host, port, address, ...args, {clientId: id})
        }

        return data
    },

    init: ()=>{
        send(...settings.read('send')[0].split(':'), '/server-ready')
    }

}

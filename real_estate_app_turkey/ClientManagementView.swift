
import SwiftUI

struct Client {
    let name: String
    let contact: String
}

struct ClientManagementView: View {
    @State private var clients = [Client(name: "John Doe", contact: "john@example.com")]
    
    var body: some View {
        List(clients, id: \.name) { client in
            VStack(alignment: .leading) {
                Text(client.name)
                Text(client.contact).font(.subheadline)
            }
        }
        .navigationTitle("Clients")
    }
}

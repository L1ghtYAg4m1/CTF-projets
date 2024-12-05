
import SwiftUI

struct MainMenuView: View {
    var body: some View {
        NavigationView {
            VStack {
                NavigationLink(destination: PropertyListView()) {
                    Text("View Properties")
                }
                .padding()
                
                NavigationLink(destination: ClientManagementView()) {
                    Text("Manage Clients")
                }
                .padding()
                
                NavigationLink(destination: PaymentView()) {
                    Text("Make a Payment")
                }
                .padding()
                
                NavigationLink(destination: FavoritesView()) {
                    Text("Favorites")
                }
                .padding()
            }
            .navigationTitle("Main Menu")
        }
    }
}

struct MainMenuView_Previews: PreviewProvider {
    static var previews: some View {
        MainMenuView()
    }
}

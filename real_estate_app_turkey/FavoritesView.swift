
import SwiftUI

struct FavoritesView: View {
    @State private var favorites = [Property]()
    
    var body: some View {
        List(favorites) { favorite in
            VStack(alignment: .leading) {
                Text(favorite.name)
                Text(favorite.price)
            }
        }
        .navigationTitle("Favorites")
    }
}

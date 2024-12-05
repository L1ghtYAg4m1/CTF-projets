
import SwiftUI

struct Property: Identifiable {
    let id = UUID()
    let name: String
    let price: String
}

struct PropertyListView: View {
    let properties = [
        Property(name: "Luxury Apartment", price: "$500,000"),
        Property(name: "Cozy Villa", price: "$1,200,000"),
        Property(name: "Modern Condo", price: "$800,000")
    ]
    
    var body: some View {
        NavigationView {
            List(properties) { property in
                VStack(alignment: .leading) {
                    Text(property.name).font(.headline)
                    Text(property.price).font(.subheadline)
                }
            }
            .navigationTitle("Property Listings")
        }
    }
}

struct PropertyListView_Previews: PreviewProvider {
    static var previews: some View {
        PropertyListView()
    }
}

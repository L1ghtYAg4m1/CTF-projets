
import SwiftUI

struct PaymentView: View {
    @State private var amount = ""
    
    var body: some View {
        VStack {
            TextField("Enter Amount", text: $amount)
                .keyboardType(.decimalPad)
                .padding()
                .textFieldStyle(RoundedBorderTextFieldStyle())
            
            Button("Make Payment") {
                // Process payment
                print("Payment of \(amount) made.")
            }
            .padding()
        }
        .navigationTitle("Payment")
    }
}

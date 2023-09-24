use proc_macro::{TokenStream};
use quote::quote;
use syn::{parse_macro_input, ItemStruct};

#[proc_macro_attribute]
pub fn event_type(_args: TokenStream, input: TokenStream) -> TokenStream {
    let input = parse_macro_input!(input as ItemStruct);
    let struct_ident = &input.ident;
    let expanded = quote! {
        #input
        impl Event for #struct_ident {

            fn as_any(&self) -> &dyn std::any::Any {
                self
            }
        }
    };
    expanded.into()
}

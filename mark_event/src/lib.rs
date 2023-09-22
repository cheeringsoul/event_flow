use proc_macro::{TokenStream};
use quote::quote;
use syn::{parse_macro_input, DeriveInput};

#[proc_macro_derive(MarkAsEvent)]
pub fn mark_as_event(_item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(_item as DeriveInput);
    let struct_ident = &input.ident;
    let expanded = quote! {
        impl Event for #struct_ident {
            fn as_any(&self) -> &dyn Any {
                self
            }
        }
    };
    TokenStream::from(expanded)
}

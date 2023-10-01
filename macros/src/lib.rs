use proc_macro::TokenStream;
use quote::quote;
use syn::{
    parse_macro_input,
    parse::{Parse, ParseStream},
    DeriveInput, Meta, Token, Ident,
};


#[proc_macro_derive(BuildEventType)]
pub fn build_event_type(_item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(_item as DeriveInput);
    let name = &input.ident;
    let expanded = quote! {
        impl Event for #name {
            fn as_any(&self) -> &dyn std::any::Any {
                self
            }
        }
    };
    TokenStream::from(expanded)
}

struct EParser {
    v: Vec<Ident>,
}

impl Parse for EParser {
    #[inline]
    fn parse(input: ParseStream) -> Result<Self, syn::Error> {
        let mut v: Vec<Ident> = vec![];
        loop {
            if input.is_empty() {
                break;
            }
            v.push(input.parse()?);
            if input.is_empty() {
                break;
            }
            input.parse::<Token!(,)>()?;
        }
        Ok(EParser { v })
    }
}

fn get_event(ast: &DeriveInput, name: &str) -> Vec<Ident> {
    let mut target: Vec<Ident> = vec![];
    for attr in &ast.attrs {
        if attr.path().is_ident(name) {
            match &attr.meta {
                Meta::List(list) => {
                    let parsed: EParser = list.parse_args().unwrap();
                    target.extend_from_slice(&parsed.v);
                }
                _ => panic!("Incorrect format for using the `{}` attribute.", name),
            }
        }
    }
    target
}
#[proc_macro_derive(PubApp, attributes(pub_event))]
pub fn pub_event_derive(input: TokenStream) -> TokenStream {
    let ast: DeriveInput = syn::parse(input).unwrap();
    let target: Vec<Ident> = get_event(&ast, "pub_event");
    let name = ast.ident;
    let expanded = quote! {
        impl AssociatedPubEvent for #name {
            fn get_associated_pub_event_ids(&self) -> Vec<std::any::TypeId> {
                vec![#(std::any::TypeId::of::<#target>()),*]
            }
        }
    };
    expanded.into()
}

#[proc_macro_derive(SubApp, attributes(sub_event, pub_event))]
pub fn sub_event_derive(input: TokenStream) -> TokenStream {
    let ast: DeriveInput = syn::parse(input).unwrap();
    let sub_target: Vec<Ident> = get_event(&ast, "sub_event");
    if sub_target.is_empty() {
        panic!("The `sub_event` attribute must be used to set at least one target.");
    }
    let pub_target: Vec<Ident> = get_event(&ast, "pub_event");
    let name = ast.ident;
    let expanded = quote! {
        impl AssociatedSubEvent for #name {
            fn get_associated_sub_event_ids(&self) -> Vec<std::any::TypeId> {
                vec![#(std::any::TypeId::of::<#sub_target>()),*]
            }
        }
        impl AssociatedPubEvent for #name {
            fn get_associated_pub_event_ids(&self) -> Vec<std::any::TypeId> {
                vec![#(std::any::TypeId::of::<#pub_target>()),*]
            }
        }
    };
    expanded.into()
}